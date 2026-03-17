from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    Numeric,
    Select,
    String,
    Table,
    Text,
    and_,
    func,
    insert,
    select,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.infrastructure.adapters.types import MainAsyncSession

_metadata = MetaData()

features_table = Table(
    "features",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("feature_name", String(255)),
)

scenarios_table = Table(
    "scenarios",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("feature_id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("scenario_name", String(255)),
)

test_runs_table = Table(
    "test_runs",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("test_plan_id", PG_UUID(as_uuid=True)),
    Column("triggered_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
    Column("status", String(16)),
    Column("scope_type", String(32)),
    Column("scope_value", String(255)),
    Column("executor_config", postgresql.JSONB(astext_type=Text())),
    Column("log_path", String(1024)),
)

test_run_results_table = Table(
    "test_run_results",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("test_run_id", PG_UUID(as_uuid=True)),
    Column("scenario_id", PG_UUID(as_uuid=True)),
    Column("feature_name", String(255)),
    Column("scenario_name", String(255)),
    Column("status", String(16)),
    Column("duration_seconds", Numeric(10, 3)),
    Column("error_message", Text),
    Column("stack_trace", Text),
)


@dataclass(slots=True, frozen=True)
class TestRunResultSpec:
    feature_name: str
    scenario_name: str
    status: str
    duration_seconds: Decimal | None
    error_message: str | None
    stack_trace: str | None
    scenario_id: UUID | None


class SqlalchemyCoverageRepository:
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def create_completed_test_run(
        self,
        *,
        project_id: UUID,
        scope_type: str,
        scope_value: str | None,
    ) -> UUID:
        now = datetime.now(tz=UTC)
        run_id = uuid4()
        stmt = insert(test_runs_table).values(
            id=run_id,
            project_id=project_id,
            test_plan_id=None,
            triggered_at=now,
            completed_at=now,
            status="completed",
            scope_type=scope_type,
            scope_value=scope_value,
            executor_config=None,
            log_path=None,
        )
        await self._session.execute(stmt)
        return run_id

    async def insert_test_run_results(
        self,
        *,
        test_run_id: UUID,
        results: list[TestRunResultSpec],
    ) -> None:
        if not results:
            return
        await self._session.execute(
            insert(test_run_results_table),
            [
                {
                    "id": uuid4(),
                    "test_run_id": test_run_id,
                    "scenario_id": item.scenario_id,
                    "feature_name": item.feature_name,
                    "scenario_name": item.scenario_name,
                    "status": item.status,
                    "duration_seconds": item.duration_seconds,
                    "error_message": item.error_message,
                    "stack_trace": item.stack_trace,
                }
                for item in results
            ],
        )

    async def find_scenario_id(
        self,
        *,
        project_id: UUID,
        feature_name: str,
        scenario_name: str,
    ) -> UUID | None:
        stmt: Select = (
            select(scenarios_table.c.id)
            .select_from(
                scenarios_table.join(
                    features_table,
                    scenarios_table.c.feature_id == features_table.c.id,
                )
            )
            .where(
                and_(
                    scenarios_table.c.project_id == project_id,
                    features_table.c.project_id == project_id,
                    features_table.c.feature_name == feature_name,
                    scenarios_table.c.scenario_name == scenario_name,
                )
            )
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_latest_scenario_status(
        self,
        *,
        project_id: UUID,
    ) -> dict[UUID, str]:
        order_key = func.coalesce(
            test_runs_table.c.completed_at,
            test_runs_table.c.triggered_at,
        )
        stmt = (
            select(
                test_run_results_table.c.scenario_id,
                test_run_results_table.c.status,
                order_key.label("run_time"),
            )
            .select_from(
                test_run_results_table.join(
                    test_runs_table,
                    test_run_results_table.c.test_run_id == test_runs_table.c.id,
                )
            )
            .where(
                test_runs_table.c.project_id == project_id,
                test_run_results_table.c.scenario_id.is_not(None),
            )
            .order_by(order_key.desc())
        )
        rows = (await self._session.execute(stmt)).mappings().all()
        mapping: dict[UUID, str] = {}
        for row in rows:
            scenario_id = row["scenario_id"]
            status = row["status"]
            if scenario_id in mapping:
                continue
            if isinstance(scenario_id, UUID) and isinstance(status, str):
                mapping[scenario_id] = status
        return mapping

    async def get_project_coverage_summary(self, *, project_id: UUID) -> dict[str, Any]:
        total_stmt = select(func.count()).select_from(scenarios_table).where(
            scenarios_table.c.project_id == project_id
        )
        total = int((await self._session.execute(total_stmt)).scalar_one())

        pass_stmt = (
            select(func.count(func.distinct(test_run_results_table.c.scenario_id)))
            .select_from(
                test_run_results_table.join(
                    test_runs_table,
                    test_run_results_table.c.test_run_id == test_runs_table.c.id,
                )
            )
            .where(
                test_runs_table.c.project_id == project_id,
                test_run_results_table.c.status == "pass",
                test_run_results_table.c.scenario_id.is_not(None),
            )
        )
        covered = int((await self._session.execute(pass_stmt)).scalar_one())

        latest_status = await self.list_latest_scenario_status(project_id=project_id)
        failed = sum(1 for status in latest_status.values() if status == "fail")

        percentage = 0.0
        if total > 0:
            percentage = round(covered / total * 100, 2)

        return {
            "total_scenarios": total,
            "covered_scenarios": covered,
            "failed_scenarios": failed,
            "coverage_percentage": percentage,
        }

    async def list_test_run_results_summary(
        self,
        *,
        test_run_id: UUID,
    ) -> dict[str, int]:
        stmt = (
            select(
                test_run_results_table.c.status,
                func.count().label("count"),
            )
            .where(test_run_results_table.c.test_run_id == test_run_id)
            .group_by(test_run_results_table.c.status)
        )
        rows = (await self._session.execute(stmt)).mappings().all()
        summary = {"pass": 0, "fail": 0, "skip": 0}
        for row in rows:
            status = row["status"]
            count = row["count"]
            if status in summary:
                summary[status] = int(count)
        return summary
