import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.bdd.execution.gateway.sqlalchemy_hybrid_repo import SqlalchemyHybridRepository
from app.bdd.execution.gateway.sqlalchemy_execution_repo import SqlalchemyExecutionRepository
from app.bdd.execution.gateway.sqlalchemy_execution_helpers import ExecutionLookupRepository
from app.bdd.execution.domain.step_auto_policy import StepAutoPolicy
from app.bdd.coverage.gateway.junit_parser import JunitParseError, parse_junit_results
from app.bdd.coverage.gateway.sqlalchemy_coverage_repo import (
    SqlalchemyCoverageRepository,
    TestRunResultSpec,
)


@dataclass(slots=True)
class HybridExecutionService:
    hybrid_repo: SqlalchemyHybridRepository
    execution_repo: SqlalchemyExecutionRepository
    coverage_repo: SqlalchemyCoverageRepository
    lookup_repo: ExecutionLookupRepository
    log_root: Path
    auto_policy: StepAutoPolicy

    async def create_execution(
        self,
        *,
        project_id: UUID,
        scenario_id: UUID,
        test_plan_item_id: UUID | None,
    ) -> dict[str, Any]:
        scenario = await self.hybrid_repo.get_scenario(
            project_id=project_id,
            scenario_id=scenario_id,
        )
        if scenario is None:
            raise ValueError("Scenario not found")

        execution = await self.hybrid_repo.create_scenario_execution(
            project_id=project_id,
            scenario_id=scenario_id,
            test_plan_item_id=test_plan_item_id,
        )
        steps = await self.hybrid_repo.list_steps(
            project_id=project_id,
            scenario_id=scenario_id,
        )
        records = await self.hybrid_repo.replace_step_execution_records(
            scenario_execution_id=execution["id"],
            step_rows=steps,
        )
        step_ids = [row["step_id"] for row in records]
        stages = await self.hybrid_repo.list_available_stages(step_ids=step_ids)

        return {
            "execution": execution,
            "records": records,
            "available_stages": stages,
        }

    async def run_auto_step(
        self,
        *,
        project_id: UUID,
        exec_id: UUID,
        record_id: UUID,
        stage_name: str,
        behave_work_dir: Path,
    ) -> dict[str, Any]:
        stage = await self.hybrid_repo.get_stage_by_name(
            project_id=project_id,
            stage_name=stage_name,
        )
        if stage is None:
            raise ValueError("Stage not found")

        log_dir = self.log_root / str(project_id)
        log_dir.mkdir(parents=True, exist_ok=True)
        junit_dir = log_dir / f"hybrid-{exec_id}-{record_id}"
        junit_dir.mkdir(parents=True, exist_ok=True)

        execution = await self.hybrid_repo.get_scenario_execution(
            project_id=project_id,
            exec_id=exec_id,
        )
        if execution is None:
            await self.hybrid_repo.update_step_record_auto(
                record_id=record_id,
                status="fail",
                stage_id=stage["id"],
                error_message="Execution not found",
            )
            return {"status": "fail", "error_message": "Execution not found"}

        scenario = await self.lookup_repo.get_scenario_with_feature(
            project_id=project_id,
            scenario_id=execution["scenario_id"],
        )
        if scenario is None:
            await self.hybrid_repo.update_step_record_auto(
                record_id=record_id,
                status="fail",
                stage_id=stage["id"],
                error_message="Scenario not found",
            )
            return {"status": "fail", "error_message": "Scenario not found"}

        scenario_name = scenario["scenario_name"]
        feature_path = scenario["file_path"]

        cmd = [
            "behave",
            "--junit",
            "--junit-directory",
            str(junit_dir),
            "--stage",
            stage_name,
            "--include",
            feature_path,
            "--name",
            scenario_name,
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(behave_work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            await process.wait()
        except Exception as exc:
            await self.hybrid_repo.update_step_record_auto(
                record_id=record_id,
                status="fail",
                stage_id=stage["id"],
                error_message=str(exc),
            )
            return {"status": "fail", "error_message": str(exc)}

        xml_files = sorted(junit_dir.glob("*.xml"))
        if not xml_files:
            await self.hybrid_repo.update_step_record_auto(
                record_id=record_id,
                status="fail",
                stage_id=stage["id"],
                error_message="Missing JUnit XML",
            )
            return {"status": "fail", "error_message": "Missing JUnit XML"}

        status = "fail"
        error_message = None
        for xml_file in xml_files:
            payload = xml_file.read_bytes()
            try:
                cases = parse_junit_results(payload)
            except JunitParseError:
                error_message = "Invalid JUnit XML"
                continue
            for case in cases:
                if case.scenario_name == scenario_name:
                    status = "pass" if case.status == "pass" else "fail"
                    error_message = case.error_message
                    break

        await self.hybrid_repo.update_step_record_auto(
            record_id=record_id,
            status=status,
            stage_id=stage["id"],
            error_message=error_message,
        )
        if status == "fail":
            await self.auto_policy.record_auto_failure(
                record_id=record_id,
                message=error_message or "auto execution failed",
            )
        return {"status": status, "error_message": error_message}

    async def update_manual_step(
        self,
        *,
        record_id: UUID,
        status: str,
        executor: str | None,
        notes: str | None,
    ) -> None:
        record = await self.hybrid_repo.get_step_record(record_id=record_id)
        if record is None:
            return
        error_message = record.get("error_message")
        if record.get("execution_mode") == "auto" and record.get("status") == "fail":
            error_message = error_message or "auto failed; manual override recorded"
        await self.hybrid_repo.update_step_record_manual(
            record_id=record_id,
            status=status,
            executor=executor,
            notes=notes,
            error_message=error_message,
        )
        keyword = record.get("keyword")
        if isinstance(keyword, str):
            await self.auto_policy.ensure_override_policy(
                record_id=record_id,
                keyword=keyword,
                manual_status=status,
            )

    async def aggregate_execution_status(self, *, exec_id: UUID) -> str:
        statuses = await self.hybrid_repo.list_step_results_for_execution(exec_id=exec_id)
        if not statuses:
            return "in_progress"
        if any(status == "fail" for status in statuses):
            return "fail"
        if all(status == "pass" for status in statuses):
            return "pass"
        if any(status == "skip" for status in statuses) and not any(
            status == "fail" for status in statuses
        ):
            return "partial"
        if any(status == "pending" for status in statuses):
            return "in_progress"
        return "partial"

    async def finalize_execution(
        self,
        *,
        exec_id: UUID,
    ) -> str:
        status = await self.aggregate_execution_status(exec_id=exec_id)
        await self.hybrid_repo.update_scenario_execution_status(
            exec_id=exec_id,
            status=status,
        )
        plan_item_id = await self.hybrid_repo.get_plan_item_for_execution(exec_id=exec_id)
        if plan_item_id is not None and status in {"pass", "fail", "partial"}:
            mapped_status = "skip" if status == "partial" else status
            await self.hybrid_repo.update_test_plan_item_status(
                item_id=plan_item_id,
                status=mapped_status,
            )
        return status
