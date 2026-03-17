from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Select,
    String,
    Table,
    Text,
    and_,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.infrastructure.adapters.types import MainAsyncSession

_metadata = MetaData()

scenarios_table = Table(
    "scenarios",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("feature_id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("scenario_name", String(255)),
)

steps_table = Table(
    "steps",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("scenario_id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("keyword", String(32)),
    Column("text", Text),
)

scenario_executions_table = Table(
    "scenario_executions",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("scenario_id", PG_UUID(as_uuid=True)),
    Column("test_plan_item_id", PG_UUID(as_uuid=True)),
    Column("status", String(16)),
    Column("created_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
)

step_execution_records_table = Table(
    "step_execution_records",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("scenario_execution_id", PG_UUID(as_uuid=True)),
    Column("step_id", PG_UUID(as_uuid=True)),
    Column("step_order", Integer),
    Column("execution_mode", String(16)),
    Column("status", String(16)),
    Column("stage_id", PG_UUID(as_uuid=True)),
    Column("executor", String(255)),
    Column("executed_at", DateTime(timezone=True)),
    Column("notes", Text),
    Column("error_message", Text),
)

step_coverages_table = Table(
    "step_coverages",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("step_id", PG_UUID(as_uuid=True)),
    Column("stage_id", PG_UUID(as_uuid=True)),
    Column("coverage_status", String(16)),
)

behave_stages_table = Table(
    "behave_stages",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("stage_name", String(64)),
)

test_plan_items_table = Table(
    "test_plan_items",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("test_plan_id", PG_UUID(as_uuid=True)),
    Column("scenario_id", PG_UUID(as_uuid=True)),
    Column("status", String(16)),
    Column("notes", Text),
    Column("updated_at", DateTime(timezone=True)),
)


test_runs_table = Table(
    "test_runs",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("log_path", String(1024)),
)


class SqlalchemyHybridRepository:
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def get_scenario(self, *, project_id: UUID, scenario_id: UUID) -> Mapping[Any, Any] | None:
        stmt: Select = select(scenarios_table).where(
            scenarios_table.c.project_id == project_id,
            scenarios_table.c.id == scenario_id,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def list_steps(self, *, project_id: UUID, scenario_id: UUID) -> list[Mapping[Any, Any]]:
        stmt = (
            select(steps_table)
            .where(
                steps_table.c.project_id == project_id,
                steps_table.c.scenario_id == scenario_id,
            )
            .order_by(steps_table.c.id.asc())
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def create_scenario_execution(
        self,
        *,
        project_id: UUID,
        scenario_id: UUID,
        test_plan_item_id: UUID | None,
    ) -> Mapping[Any, Any]:
        now = datetime.now(tz=UTC)
        exec_id = uuid4()
        stmt = insert(scenario_executions_table).values(
            id=exec_id,
            project_id=project_id,
            scenario_id=scenario_id,
            test_plan_item_id=test_plan_item_id,
            status="in_progress",
            created_at=now,
            completed_at=None,
        )
        await self._session.execute(stmt)
        return await self.get_scenario_execution(project_id=project_id, exec_id=exec_id)

    async def get_scenario_execution(
        self,
        *,
        project_id: UUID,
        exec_id: UUID,
    ) -> Mapping[Any, Any] | None:
        stmt: Select = select(scenario_executions_table).where(
            scenario_executions_table.c.project_id == project_id,
            scenario_executions_table.c.id == exec_id,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def replace_step_execution_records(
        self,
        *,
        scenario_execution_id: UUID,
        step_rows: list[Mapping[Any, Any]],
    ) -> list[Mapping[Any, Any]]:
        await self._session.execute(
            delete(step_execution_records_table).where(
                step_execution_records_table.c.scenario_execution_id == scenario_execution_id
            )
        )
        now = datetime.now(tz=UTC)
        records = []
        for idx, step in enumerate(step_rows, start=1):
            record_id = uuid4()
            stmt = insert(step_execution_records_table).values(
                id=record_id,
                scenario_execution_id=scenario_execution_id,
                step_id=step["id"],
                step_order=idx,
                execution_mode="auto",
                status="pending",
                stage_id=None,
                executor=None,
                executed_at=None,
                notes=None,
                error_message=None,
            )
            await self._session.execute(stmt)
            records.append(
                {
                    "id": record_id,
                    "scenario_execution_id": scenario_execution_id,
                    "step_id": step["id"],
                    "step_order": idx,
                    "execution_mode": "auto",
                    "status": "pending",
                    "stage_id": None,
                    "executor": None,
                    "executed_at": None,
                    "notes": None,
                    "error_message": None,
                    "keyword": step["keyword"],
                    "text": step["text"],
                }
            )
        return records

    async def list_step_execution_records(
        self,
        *,
        scenario_execution_id: UUID,
    ) -> list[Mapping[Any, Any]]:
        stmt = (
            select(step_execution_records_table)
            .where(step_execution_records_table.c.scenario_execution_id == scenario_execution_id)
            .order_by(step_execution_records_table.c.step_order.asc())
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def list_available_stages(self, *, step_ids: list[UUID]) -> dict[UUID, list[str]]:
        if not step_ids:
            return {}
        stmt = (
            select(step_coverages_table.c.step_id, behave_stages_table.c.stage_name)
            .select_from(
                step_coverages_table.join(
                    behave_stages_table,
                    step_coverages_table.c.stage_id == behave_stages_table.c.id,
                )
            )
            .where(
                step_coverages_table.c.step_id.in_(step_ids),
                step_coverages_table.c.coverage_status == "covered",
            )
            .order_by(step_coverages_table.c.step_id.asc())
        )
        rows = (await self._session.execute(stmt)).mappings().all()
        mapping: dict[UUID, list[str]] = {}
        for row in rows:
            step_id = row["step_id"]
            stage_name = row["stage_name"]
            if not isinstance(step_id, UUID) or not isinstance(stage_name, str):
                continue
            mapping.setdefault(step_id, []).append(stage_name)
        return mapping

    async def update_step_record_manual(
        self,
        *,
        record_id: UUID,
        status: str,
        executor: str | None,
        notes: str | None,
        error_message: str | None = None,
    ) -> Mapping[Any, Any] | None:
        stmt = (
            update(step_execution_records_table)
            .where(step_execution_records_table.c.id == record_id)
            .values(
                execution_mode="manual",
                status=status,
                executor=executor,
                executed_at=datetime.now(tz=UTC),
                notes=notes,
                error_message=error_message,
            )
        )
        await self._session.execute(stmt)
        stmt_fetch = select(step_execution_records_table).where(
            step_execution_records_table.c.id == record_id
        )
        return (await self._session.execute(stmt_fetch)).mappings().one_or_none()

    async def update_step_record_auto(
        self,
        *,
        record_id: UUID,
        status: str,
        stage_id: UUID | None,
        error_message: str | None,
    ) -> Mapping[Any, Any] | None:
        stmt = (
            update(step_execution_records_table)
            .where(step_execution_records_table.c.id == record_id)
            .values(
                execution_mode="auto",
                status=status,
                stage_id=stage_id,
                executed_at=datetime.now(tz=UTC),
                error_message=error_message,
            )
        )
        await self._session.execute(stmt)
        stmt_fetch = select(step_execution_records_table).where(
            step_execution_records_table.c.id == record_id
        )
        return (await self._session.execute(stmt_fetch)).mappings().one_or_none()

    async def update_scenario_execution_status(
        self,
        *,
        exec_id: UUID,
        status: str,
    ) -> None:
        completed_at = datetime.now(tz=UTC) if status in {"pass", "fail", "partial"} else None
        stmt = (
            update(scenario_executions_table)
            .where(scenario_executions_table.c.id == exec_id)
            .values(status=status, completed_at=completed_at)
        )
        await self._session.execute(stmt)

    async def update_test_plan_item_status(
        self,
        *,
        item_id: UUID,
        status: str,
    ) -> None:
        stmt = (
            update(test_plan_items_table)
            .where(test_plan_items_table.c.id == item_id)
            .values(status=status, updated_at=datetime.now(tz=UTC))
        )
        await self._session.execute(stmt)

    async def list_execution_steps_with_text(
        self,
        *,
        exec_id: UUID,
    ) -> list[Mapping[Any, Any]]:
        stmt = (
            select(
                step_execution_records_table.c.id,
                step_execution_records_table.c.step_id,
                step_execution_records_table.c.step_order,
                step_execution_records_table.c.execution_mode,
                step_execution_records_table.c.status,
                step_execution_records_table.c.stage_id,
                step_execution_records_table.c.executor,
                step_execution_records_table.c.executed_at,
                step_execution_records_table.c.notes,
                step_execution_records_table.c.error_message,
                steps_table.c.keyword,
                steps_table.c.text,
            )
            .select_from(
                step_execution_records_table.join(
                    steps_table,
                    step_execution_records_table.c.step_id == steps_table.c.id,
                )
            )
            .where(step_execution_records_table.c.scenario_execution_id == exec_id)
            .order_by(step_execution_records_table.c.step_order.asc())
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def get_plan_item_for_execution(
        self,
        *,
        exec_id: UUID,
    ) -> UUID | None:
        stmt = select(scenario_executions_table.c.test_plan_item_id).where(
            scenario_executions_table.c.id == exec_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_stage_by_name(
        self,
        *,
        project_id: UUID,
        stage_name: str,
    ) -> Mapping[Any, Any] | None:
        stmt = select(behave_stages_table).where(
            behave_stages_table.c.project_id == project_id,
            behave_stages_table.c.stage_name == stage_name,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def append_step_error(
        self,
        *,
        record_id: UUID,
        message: str,
    ) -> None:
        stmt = (
            update(step_execution_records_table)
            .where(step_execution_records_table.c.id == record_id)
            .values(error_message=message)
        )
        await self._session.execute(stmt)

    async def list_step_results_for_execution(
        self,
        *,
        exec_id: UUID,
    ) -> list[str]:
        stmt = select(step_execution_records_table.c.status).where(
            step_execution_records_table.c.scenario_execution_id == exec_id
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [status for status in rows if isinstance(status, str)]

    async def get_step_record(self, *, record_id: UUID) -> Mapping[Any, Any] | None:
        stmt = (
            select(
                step_execution_records_table.c.id,
                step_execution_records_table.c.execution_mode,
                step_execution_records_table.c.status,
                step_execution_records_table.c.error_message,
                steps_table.c.keyword,
            )
            .select_from(
                step_execution_records_table.join(
                    steps_table,
                    step_execution_records_table.c.step_id == steps_table.c.id,
                )
            )
            .where(step_execution_records_table.c.id == record_id)
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()
