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
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.bdd.features.domain.feature_repository import (
    BehaveStageSpec,
    FeatureRepository,
    FeatureSyncSummary,
    StepCoverageSpec,
    SyncFeatureFile,
)
from app.infrastructure.adapters.types import MainAsyncSession

_metadata = MetaData()

features_table = Table(
    "features",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("file_path", String(1024)),
    Column("git_sha", String(64)),
    Column("content", Text),
    Column("feature_name", String(255)),
    Column("parent_feature_id", PG_UUID(as_uuid=True)),
    Column("depth", Integer),
    Column("parsed_at", DateTime(timezone=True)),
)

scenarios_table = Table(
    "scenarios",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("feature_id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("rule_name", String(255)),
    Column("scenario_name", String(255)),
    Column("tags", postgresql.JSONB(astext_type=Text())),
    Column("line_number", Integer),
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

behave_stages_table = Table(
    "behave_stages",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True)),
    Column("stage_name", String(64)),
    Column("steps_dir_path", String(1024)),
)

step_coverages_table = Table(
    "step_coverages",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("step_id", PG_UUID(as_uuid=True)),
    Column("stage_id", PG_UUID(as_uuid=True)),
    Column("coverage_status", String(16)),
)


class SqlalchemyFeatureRepository(FeatureRepository):
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def replace_project_features(
        self,
        *,
        project_id: UUID,
        files: list[SyncFeatureFile],
    ) -> FeatureSyncSummary:
        existing_stmt: Select = select(
            features_table.c.id,
            features_table.c.file_path,
        ).where(features_table.c.project_id == project_id)
        existing_rows = (await self._session.execute(existing_stmt)).mappings().all()
        existing_by_path = {
            row["file_path"]: row["id"]
            for row in existing_rows
            if self._is_non_empty_str(row.get("file_path"))
        }

        incoming_paths = {item.file_path for item in files}
        now = datetime.now(tz=UTC)

        path_to_id: dict[str, UUID] = dict(existing_by_path)
        for item in files:
            if item.file_path not in path_to_id:
                path_to_id[item.file_path] = uuid4()

        added = 0
        updated = 0

        for item in files:
            existing_id = existing_by_path.get(item.file_path)
            current_id = path_to_id[item.file_path]
            parent_feature_id = (
                path_to_id[item.parent_file_path]
                if item.parent_file_path is not None
                else None
            )
            if existing_id is None:
                stmt = insert(features_table).values(
                    id=current_id,
                    project_id=project_id,
                    file_path=item.file_path,
                    git_sha=item.git_sha,
                    content=item.content,
                    feature_name=item.feature_name,
                    parent_feature_id=parent_feature_id,
                    depth=item.depth,
                    parsed_at=now,
                )
                await self._session.execute(stmt)
                added += 1
            else:
                stmt = (
                    update(features_table)
                    .where(features_table.c.id == existing_id)
                    .values(
                        git_sha=item.git_sha,
                        content=item.content,
                        feature_name=item.feature_name,
                        parent_feature_id=parent_feature_id,
                        depth=item.depth,
                        parsed_at=now,
                    )
                )
                await self._session.execute(stmt)
                updated += 1

        deleted = 0
        if existing_by_path:
            stale_paths = set(existing_by_path).difference(incoming_paths)
            if stale_paths:
                stmt = delete(features_table).where(
                    features_table.c.project_id == project_id,
                    features_table.c.file_path.in_(stale_paths),
                )
                deleted_result = await self._session.execute(stmt)
                deleted = deleted_result.rowcount or 0

        await self._replace_scenarios_and_steps(
            project_id=project_id,
            files=files,
            path_to_id=path_to_id,
        )

        return FeatureSyncSummary(
            added=added,
            updated=updated,
            deleted=deleted,
            total=len(files),
            synced_at=now,
        )

    async def _replace_scenarios_and_steps(
        self,
        *,
        project_id: UUID,
        files: list[SyncFeatureFile],
        path_to_id: dict[str, UUID],
    ) -> None:
        await self._session.execute(
            delete(steps_table).where(steps_table.c.project_id == project_id)
        )
        await self._session.execute(
            delete(scenarios_table).where(scenarios_table.c.project_id == project_id)
        )

        for file in files:
            feature_id = path_to_id[file.file_path]
            for scenario in file.scenarios:
                scenario_id = uuid4()
                await self._session.execute(
                    insert(scenarios_table).values(
                        id=scenario_id,
                        feature_id=feature_id,
                        project_id=project_id,
                        rule_name=scenario.rule_name,
                        scenario_name=scenario.scenario_name,
                        tags=scenario.tags,
                        line_number=scenario.line_number,
                    )
                )
                for step in scenario.steps:
                    await self._session.execute(
                        insert(steps_table).values(
                            id=uuid4(),
                            scenario_id=scenario_id,
                            project_id=project_id,
                            keyword=step.keyword,
                            text=step.text,
                        )
                    )

    async def list_features_by_project(
        self,
        *,
        project_id: UUID,
    ) -> list[Mapping[Any, Any]]:
        stmt = (
            select(features_table)
            .where(features_table.c.project_id == project_id)
            .order_by(features_table.c.depth.asc(), features_table.c.file_path.asc())
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def list_scenarios_by_project(
        self,
        *,
        project_id: UUID,
    ) -> list[Mapping[Any, Any]]:
        stmt = (
            select(scenarios_table)
            .where(scenarios_table.c.project_id == project_id)
            .order_by(
                scenarios_table.c.feature_id.asc(),
                scenarios_table.c.line_number.asc(),
                scenarios_table.c.scenario_name.asc(),
            )
        )
        return (await self._session.execute(stmt)).mappings().all()

    async def list_steps_by_project(
        self,
        *,
        project_id: UUID,
    ) -> list[Mapping[Any, Any]]:
        stmt = select(
            steps_table.c.id,
            steps_table.c.keyword,
            steps_table.c.text,
        ).where(steps_table.c.project_id == project_id)
        return (await self._session.execute(stmt)).mappings().all()

    async def get_feature_by_project(
        self,
        *,
        project_id: UUID,
        feature_id: UUID,
    ) -> Mapping[Any, Any] | None:
        stmt = select(features_table).where(
            features_table.c.project_id == project_id,
            features_table.c.id == feature_id,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def replace_behave_stages(
        self,
        *,
        project_id: UUID,
        stages: list[BehaveStageSpec],
    ) -> dict[str, UUID]:
        stage_ids_stmt = select(behave_stages_table.c.id).where(
            behave_stages_table.c.project_id == project_id
        )
        stage_ids = (await self._session.execute(stage_ids_stmt)).scalars().all()
        if stage_ids:
            await self._session.execute(
                delete(step_coverages_table).where(
                    step_coverages_table.c.stage_id.in_(stage_ids)
                )
            )
        await self._session.execute(
            delete(behave_stages_table).where(
                behave_stages_table.c.project_id == project_id
            )
        )

        mapping: dict[str, UUID] = {}
        for stage in stages:
            stage_id = uuid4()
            mapping[stage.stage_name] = stage_id
            await self._session.execute(
                insert(behave_stages_table).values(
                    id=stage_id,
                    project_id=project_id,
                    stage_name=stage.stage_name,
                    steps_dir_path=stage.steps_dir_path,
                )
            )
        return mapping

    async def replace_step_coverages(
        self,
        *,
        project_id: UUID,
        coverages: list[StepCoverageSpec],
    ) -> None:
        step_ids_stmt = select(steps_table.c.id).where(
            steps_table.c.project_id == project_id
        )
        step_ids = (await self._session.execute(step_ids_stmt)).scalars().all()
        if step_ids:
            await self._session.execute(
                delete(step_coverages_table).where(
                    step_coverages_table.c.step_id.in_(step_ids)
                )
            )

        if not coverages:
            return

        await self._session.execute(
            insert(step_coverages_table),
            [
                {
                    "id": uuid4(),
                    "step_id": item.step_id,
                    "stage_id": item.stage_id,
                    "coverage_status": item.coverage_status,
                }
                for item in coverages
            ],
        )

    async def list_available_stages_by_step_ids(
        self,
        *,
        step_ids: list[UUID],
    ) -> dict[UUID, list[str]]:
        if not step_ids:
            return {}

        stmt = (
            select(
                step_coverages_table.c.step_id,
                behave_stages_table.c.stage_name,
            )
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
            .order_by(
                step_coverages_table.c.step_id.asc(),
                behave_stages_table.c.stage_name.asc(),
            )
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

    async def get_feature_by_path(
        self,
        *,
        project_id: UUID,
        file_path: str,
    ) -> Mapping[Any, Any] | None:
        stmt = select(features_table).where(
            features_table.c.project_id == project_id,
            features_table.c.file_path == file_path,
        )
        return (await self._session.execute(stmt)).mappings().one_or_none()

    async def suggest_steps(
        self,
        *,
        project_id: UUID,
        prefix: str,
        limit: int = 20,
    ) -> list[Mapping[Any, Any]]:
        stmt = (
            select(steps_table.c.keyword, steps_table.c.text)
            .where(
                steps_table.c.project_id == project_id,
                steps_table.c.text.ilike(f"{prefix}%"),
            )
            .distinct()
            .order_by(steps_table.c.keyword.asc(), steps_table.c.text.asc())
            .limit(limit)
        )
        return (await self._session.execute(stmt)).mappings().all()

    @staticmethod
    def _is_non_empty_str(value: Any) -> bool:
        return isinstance(value, str) and len(value) > 0
