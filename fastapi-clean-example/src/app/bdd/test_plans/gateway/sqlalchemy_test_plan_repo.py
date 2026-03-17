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
    delete,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.adapters.types import MainAsyncSession

_metadata = MetaData()

test_plans_table = Table(
    "test_plans",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("name", String(255)),
    Column("description", Text),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
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

test_run_results_table = Table(
    "test_run_results",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("test_run_id", PG_UUID(as_uuid=True)),
    Column("scenario_id", PG_UUID(as_uuid=True)),
    Column("status", String(16)),
)


test_runs_table = Table(
    "test_runs",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
)


class SqlalchemyTestPlanRepository:
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def list_test_plans(self, *, project_id: UUID) -> list[Mapping[Any, Any]]:
        stmt: Select = (
            select(test_plans_table)
            .where(test_plans_table.c.project_id == project_id)
            .order_by(test_plans_table.c.created_at.desc())
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def create_test_plan(
        self,
        *,
        project_id: UUID,
        name: str,
        description: str | None,
    ) -> Mapping[Any, Any]:
        now = datetime.now(tz=UTC)
        plan_id = uuid4()
        stmt = pg_insert(test_plans_table).values(
            id=plan_id,
            project_id=project_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
        await self._session.execute(stmt)
        return await self.get_test_plan(project_id=project_id, plan_id=plan_id)

    async def get_test_plan(
        self,
        *,
        project_id: UUID,
        plan_id: UUID,
    ) -> Mapping[Any, Any] | None:
        stmt: Select = select(test_plans_table).where(
            test_plans_table.c.project_id == project_id,
            test_plans_table.c.id == plan_id,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def update_test_plan(
        self,
        *,
        project_id: UUID,
        plan_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Mapping[Any, Any] | None:
        values: dict[str, object] = {"updated_at": datetime.now(tz=UTC)}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description

        stmt = (
            update(test_plans_table)
            .where(
                test_plans_table.c.project_id == project_id,
                test_plans_table.c.id == plan_id,
            )
            .values(**values)
        )
        await self._session.execute(stmt)
        return await self.get_test_plan(project_id=project_id, plan_id=plan_id)

    async def delete_test_plan(self, *, project_id: UUID, plan_id: UUID) -> bool:
        await self._session.execute(
            delete(test_plan_items_table).where(
                test_plan_items_table.c.test_plan_id == plan_id
            )
        )
        stmt = (
            delete(test_plans_table)
            .where(
                test_plans_table.c.project_id == project_id,
                test_plans_table.c.id == plan_id,
            )
            .returning(test_plans_table.c.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_items(
        self,
        *,
        project_id: UUID,
        plan_id: UUID,
    ) -> list[Mapping[Any, Any]]:
        stmt = (
            select(test_plan_items_table)
            .select_from(
                test_plan_items_table.join(
                    test_plans_table,
                    test_plan_items_table.c.test_plan_id == test_plans_table.c.id,
                )
            )
            .where(
                test_plans_table.c.project_id == project_id,
                test_plan_items_table.c.test_plan_id == plan_id,
            )
            .order_by(test_plan_items_table.c.updated_at.desc())
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def add_items(
        self,
        *,
        plan_id: UUID,
        scenario_ids: list[UUID],
    ) -> dict[str, int]:
        if not scenario_ids:
            return {"added": 0, "skipped": 0}
        now = datetime.now(tz=UTC)
        stmt = (
            pg_insert(test_plan_items_table)
            .values(
                [
                    {
                        "id": uuid4(),
                        "test_plan_id": plan_id,
                        "scenario_id": scenario_id,
                        "status": "not_run",
                        "notes": None,
                        "updated_at": now,
                    }
                    for scenario_id in scenario_ids
                ]
            )
            .on_conflict_do_nothing(
                index_elements=[
                    test_plan_items_table.c.test_plan_id,
                    test_plan_items_table.c.scenario_id,
                ]
            )
            .returning(test_plan_items_table.c.id)
        )
        result = await self._session.execute(stmt)
        inserted = result.scalars().all()
        return {"added": len(inserted), "skipped": len(scenario_ids) - len(inserted)}

    async def update_item_status(
        self,
        *,
        project_id: UUID,
        plan_id: UUID,
        item_id: UUID,
        status: str,
        notes: str | None,
    ) -> Mapping[Any, Any] | None:
        values: dict[str, object] = {
            "status": status,
            "updated_at": datetime.now(tz=UTC),
        }
        if notes is not None:
            values["notes"] = notes

        stmt = (
            update(test_plan_items_table)
            .where(
                test_plan_items_table.c.id == item_id,
                test_plan_items_table.c.test_plan_id == plan_id,
            )
            .values(**values)
        )
        await self._session.execute(stmt)

        stmt_fetch = (
            select(test_plan_items_table)
            .select_from(
                test_plan_items_table.join(
                    test_plans_table,
                    test_plan_items_table.c.test_plan_id == test_plans_table.c.id,
                )
            )
            .where(
                test_plans_table.c.project_id == project_id,
                test_plan_items_table.c.id == item_id,
            )
        )
        return (await self._session.execute(stmt_fetch)).mappings().one_or_none()

    async def get_progress(
        self,
        *,
        project_id: UUID,
        plan_id: UUID,
    ) -> dict[str, int]:
        stmt = (
            select(
                test_plan_items_table.c.status,
                func.count().label("count"),
            )
            .select_from(
                test_plan_items_table.join(
                    test_plans_table,
                    test_plan_items_table.c.test_plan_id == test_plans_table.c.id,
                )
            )
            .where(
                test_plans_table.c.project_id == project_id,
                test_plan_items_table.c.test_plan_id == plan_id,
            )
            .group_by(test_plan_items_table.c.status)
        )
        rows = (await self._session.execute(stmt)).mappings().all()
        summary = {
            "total": 0,
            "not_run": 0,
            "pass": 0,
            "fail": 0,
            "skip": 0,
            "blocked": 0,
        }
        for row in rows:
            status = row["status"]
            count = int(row["count"])
            summary["total"] += count
            if status in summary:
                summary[status] += count
        return summary

    async def sync_items_from_test_run(
        self,
        *,
        project_id: UUID,
        plan_id: UUID,
        test_run_id: UUID,
    ) -> dict[str, int]:
        plan_stmt = select(test_plans_table.c.id).where(
            test_plans_table.c.project_id == project_id,
            test_plans_table.c.id == plan_id,
        )
        if (await self._session.execute(plan_stmt)).scalar_one_or_none() is None:
            return {"updated": 0, "skipped": 0}

        run_stmt = select(test_runs_table.c.id).where(
            test_runs_table.c.project_id == project_id,
            test_runs_table.c.id == test_run_id,
        )
        if (await self._session.execute(run_stmt)).scalar_one_or_none() is None:
            return {"updated": 0, "skipped": 0}

        results_stmt = select(
            test_run_results_table.c.scenario_id,
            test_run_results_table.c.status,
        ).where(
            test_run_results_table.c.test_run_id == test_run_id,
            test_run_results_table.c.scenario_id.is_not(None),
        )
        results = (await self._session.execute(results_stmt)).mappings().all()
        if not results:
            return {"updated": 0, "skipped": 0}

        now = datetime.now(tz=UTC)
        updated = 0
        skipped = 0
        for row in results:
            scenario_id = row["scenario_id"]
            status = row["status"]
            if not isinstance(scenario_id, UUID) or not isinstance(status, str):
                skipped += 1
                continue
            if status not in {"pass", "fail", "skip"}:
                skipped += 1
                continue
            stmt = (
                update(test_plan_items_table)
                .where(
                    test_plan_items_table.c.test_plan_id == plan_id,
                    test_plan_items_table.c.scenario_id == scenario_id,
                )
                .values(status=status, updated_at=now)
            )
            result = await self._session.execute(stmt)
            updated += result.rowcount or 0

        return {"updated": updated, "skipped": skipped}
