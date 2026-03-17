import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import UUID

from app.bdd.coverage.gateway.junit_parser import JunitParseError, parse_junit_results
from app.bdd.coverage.gateway.sqlalchemy_coverage_repo import (
    SqlalchemyCoverageRepository,
    TestRunResultSpec,
)
from app.bdd.execution.gateway.sqlalchemy_execution_repo import (
    SqlalchemyExecutionRepository,
)
from app.infrastructure.adapters.types import MainAsyncSession

_LOG_QUEUES: dict[UUID, asyncio.Queue[str]] = {}


def get_log_queue(test_run_id: UUID) -> asyncio.Queue[str]:
    queue = _LOG_QUEUES.get(test_run_id)
    if queue is None:
        queue = asyncio.Queue()
        _LOG_QUEUES[test_run_id] = queue
    return queue


def drop_log_queue(test_run_id: UUID) -> None:
    _LOG_QUEUES.pop(test_run_id, None)


def make_done_event() -> str:
    return "event: done\ndata: {}\n\n"


async def stream_log_queue(
    test_run_id: UUID,
) -> AsyncGenerator[str, None]:
    queue = get_log_queue(test_run_id)
    while True:
        line = await queue.get()
        if line == "__DONE__":
            break
        yield f"data: {line.rstrip()}\n\n"
    yield make_done_event()


class BehaveRunner:
    def __init__(
        self,
        *,
        session: MainAsyncSession,
        execution_repo: SqlalchemyExecutionRepository,
        coverage_repo: SqlalchemyCoverageRepository,
        log_root: Path,
    ) -> None:
        self._session = session
        self._execution_repo = execution_repo
        self._coverage_repo = coverage_repo
        self._log_root = log_root

    async def run(
        self,
        *,
        project_id: UUID,
        test_run_id: UUID,
        behave_work_dir: Path,
        scope_type: str,
        scope_value: str | None,
        executor_config: dict[str, Any] | None,
    ) -> None:
        log_dir = self._log_root / str(project_id)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{test_run_id}.log"
        junit_dir = log_dir / f"{test_run_id}-junit"
        junit_dir.mkdir(parents=True, exist_ok=True)

        await self._execution_repo.update_test_run_status(
            test_run_id=test_run_id,
            status="running",
            log_path=str(log_path),
        )
        await self._session.commit()

        queue = get_log_queue(test_run_id)
        cmd = ["behave", "--junit", "--junit-directory", str(junit_dir)]
        if scope_type == "feature" and scope_value:
            cmd.extend([scope_value])
        if scope_type == "tag" and scope_value:
            cmd.extend(["--tags", scope_value])

        env = None
        if executor_config:
            env = os.environ.copy()
            env.update({k: str(v) for k, v in executor_config.items()})

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(behave_work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )
        except Exception as exc:  # pragma: no cover - subprocess start failure
            await self._execution_repo.update_test_run_status(
                test_run_id=test_run_id,
                status="failed",
                completed_at=datetime.now(tz=UTC),
            )
            await self._session.commit()
            await queue.put(f"failed to start behave: {exc}\n")
            await queue.put("__DONE__")
            drop_log_queue(test_run_id)
            return

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._capture_output(process, log_path, queue))
            tg.create_task(
                self._wait_and_finalize(
                    process,
                    test_run_id,
                    project_id,
                    junit_dir,
                )
            )

        await queue.put("__DONE__")
        drop_log_queue(test_run_id)

    async def _capture_output(
        self,
        process: asyncio.subprocess.Process,
        log_path: Path,
        queue: asyncio.Queue[str],
    ) -> None:
        if process.stdout is None:
            return
        with log_path.open("a", encoding="utf-8") as handle:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                handle.write(text)
                handle.flush()
                await queue.put(text)

    async def _wait_and_finalize(
        self,
        process: asyncio.subprocess.Process,
        test_run_id: UUID,
        project_id: UUID,
        junit_dir: Path,
    ) -> None:
        await process.wait()

        xml_files = sorted(junit_dir.glob("*.xml"))
        if not xml_files:
            await self._execution_repo.update_test_run_status(
                test_run_id=test_run_id,
                status="failed",
                completed_at=datetime.now(tz=UTC),
            )
            await self._session.commit()
            return

        results: list[TestRunResultSpec] = []
        for xml_file in xml_files:
            payload = xml_file.read_bytes()
            try:
                cases = parse_junit_results(payload)
            except JunitParseError:
                await self._execution_repo.update_test_run_status(
                    test_run_id=test_run_id,
                    status="failed",
                    completed_at=datetime.now(tz=UTC),
                )
                await self._session.commit()
                return

            for case in cases:
                scenario_id = await self._coverage_repo.find_scenario_id(
                    project_id=project_id,
                    feature_name=case.feature_name,
                    scenario_name=case.scenario_name,
                )
                results.append(
                    TestRunResultSpec(
                        feature_name=case.feature_name,
                        scenario_name=case.scenario_name,
                        status=case.status,
                        duration_seconds=case.duration_seconds,
                        error_message=case.error_message,
                        stack_trace=case.stack_trace,
                        scenario_id=scenario_id,
                    )
                )

        await self._coverage_repo.insert_test_run_results(
            test_run_id=test_run_id,
            results=results,
        )
        await self._execution_repo.update_test_run_status(
            test_run_id=test_run_id,
            status="completed",
            completed_at=datetime.now(tz=UTC),
        )
        await self._session.commit()
