from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    Select,
    String,
    Table,
    Text,
    and_,
    insert,
    select,
    update,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.infrastructure.adapters.types import MainAsyncSession

_metadata = MetaData()

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

project_behave_configs_table = Table(
    "project_behave_configs",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("behave_work_dir", String(1024)),
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
    Column("duration_seconds", NUMERIC(10, 3)),
    Column("error_message", Text),
    Column("stack_trace", Text),
)


class SqlalchemyExecutionRepository:
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def get_behave_config(self, *, project_id: UUID) -> Mapping[Any, Any] | None:
        stmt: Select = select(project_behave_configs_table).where(
            project_behave_configs_table.c.project_id == project_id
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def has_running_test_run(self, *, project_id: UUID) -> bool:
        stmt: Select = select(test_runs_table.c.id).where(
            and_(
                test_runs_table.c.project_id == project_id,
                test_runs_table.c.status.in_(["pending", "running"]),
            )
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def create_pending_test_run(
        self,
        *,
        project_id: UUID,
        scope_type: str,
        scope_value: str | None,
        executor_config: dict[str, Any] | None,
        test_plan_id: UUID | None = None,
    ) -> Mapping[Any, Any]:
        now = datetime.now(tz=UTC)
        run_id = uuid4()
        stmt = insert(test_runs_table).values(
            id=run_id,
            project_id=project_id,
            test_plan_id=test_plan_id,
            triggered_at=now,
            completed_at=None,
            status="pending",
            scope_type=scope_type,
            scope_value=scope_value,
            executor_config=executor_config,
            log_path=None,
        )
        await self._session.execute(stmt)
        return await self.get_test_run(project_id=project_id, test_run_id=run_id)

    async def get_test_run(
        self,
        *,
        project_id: UUID,
        test_run_id: UUID,
    ) -> Mapping[Any, Any] | None:
        stmt: Select = select(test_runs_table).where(
            test_runs_table.c.project_id == project_id,
            test_runs_table.c.id == test_run_id,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def update_test_run_status(
        self,
        *,
        test_run_id: UUID,
        status: str,
        completed_at: datetime | None = None,
        log_path: str | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if completed_at is not None:
            values["completed_at"] = completed_at
        if log_path is not None:
            values["log_path"] = log_path
        stmt = (
            update(test_runs_table)
            .where(test_runs_table.c.id == test_run_id)
            .values(**values)
        )
        await self._session.execute(stmt)
