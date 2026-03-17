from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import MetaData, Select, Table, Column, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import select

from app.infrastructure.adapters.types import MainAsyncSession

_metadata = MetaData()

features_table = Table(
    "features",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("file_path", String(1024)),
)

scenarios_table = Table(
    "scenarios",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("feature_id", PG_UUID(as_uuid=True)),
    Column("scenario_name", String(255)),
)


class ExecutionLookupRepository:
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def get_scenario_with_feature(
        self,
        *,
        project_id: UUID,
        scenario_id: UUID,
    ) -> Mapping | None:
        stmt: Select = (
            select(
                scenarios_table.c.id,
                scenarios_table.c.scenario_name,
                scenarios_table.c.feature_id,
                features_table.c.file_path,
            )
            .select_from(
                scenarios_table.join(
                    features_table,
                    scenarios_table.c.feature_id == features_table.c.id,
                )
            )
            .where(
                scenarios_table.c.project_id == project_id,
                scenarios_table.c.id == scenario_id,
            )
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()
