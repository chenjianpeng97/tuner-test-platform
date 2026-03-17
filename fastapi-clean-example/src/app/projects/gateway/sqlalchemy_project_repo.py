from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    LargeBinary,
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
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import ProgrammingError

from app.infrastructure.adapters.types import MainAsyncSession
from app.projects.domain.project import Project, ProjectGitConfig
from app.projects.domain.project_repository import ProjectRepository

_metadata = MetaData()

projects_table = Table(
    "projects",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("name", String(120)),
    Column("description", Text),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)

project_git_configs_table = Table(
    "project_git_configs",
    _metadata,
    Column("id", PG_UUID(as_uuid=True)),
    Column("project_id", PG_UUID(as_uuid=True), ForeignKey("projects.id")),
    Column("git_repo_url", String(512)),
    Column("git_branch", String(128)),
    Column("git_access_token_encrypted", LargeBinary),
    Column("features_root", String(255)),
)


class SqlalchemyProjectRepository(ProjectRepository):
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session

    async def list_projects(self) -> list[Project]:
        stmt: Select = select(projects_table).order_by(
            projects_table.c.created_at.desc()
        )
        rows = (await self._session.execute(stmt)).mappings().all()
        return [self._to_project(row) for row in rows]

    async def get_project(self, project_id: UUID) -> Project | None:
        stmt: Select = select(projects_table).where(projects_table.c.id == project_id)
        row = (await self._session.execute(stmt)).mappings().one_or_none()
        return self._to_project(row) if row else None

    async def create_project(self, *, name: str, description: str | None) -> Project:
        now = datetime.now(tz=UTC)
        new_id = uuid4()
        stmt = insert(projects_table).values(
            id=new_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
        await self._session.execute(stmt)
        return Project(
            id=new_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )

    async def update_project(
        self,
        *,
        project_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project | None:
        existing = await self.get_project(project_id)
        if existing is None:
            return None

        values: dict[str, object] = {"updated_at": datetime.now(tz=UTC)}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description

        stmt = (
            update(projects_table)
            .where(projects_table.c.id == project_id)
            .values(**values)
        )
        await self._session.execute(stmt)
        return await self.get_project(project_id)

    async def delete_project(self, project_id: UUID) -> bool:
        stmt = (
            delete(projects_table)
            .where(projects_table.c.id == project_id)
            .returning(projects_table.c.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_git_config(self, project_id: UUID) -> ProjectGitConfig | None:
        stmt: Select = select(project_git_configs_table).where(
            project_git_configs_table.c.project_id == project_id
        )
        try:
            row = (await self._session.execute(stmt)).mappings().one_or_none()
        except ProgrammingError as exc:
            if not self._is_legacy_features_root_error(exc):
                raise
            await self._session.rollback()
            row = (
                await self._session.execute(self._legacy_git_config_select(project_id))
            ).mappings().one_or_none()
        if row is None:
            return None
        return self._to_git_config(row)

    async def upsert_git_config(
        self,
        *,
        project_id: UUID,
        git_repo_url: str,
        git_branch: str,
        git_access_token_encrypted: bytes,
        features_root: str,
    ) -> ProjectGitConfig | None:
        project = await self.get_project(project_id)
        if project is None:
            return None

        existing = await self.get_git_config(project_id)
        if existing is None:
            stmt = insert(project_git_configs_table).values(
                id=uuid4(),
                project_id=project_id,
                git_repo_url=git_repo_url,
                git_branch=git_branch,
                git_access_token_encrypted=git_access_token_encrypted,
                features_root=features_root,
            )
        else:
            stmt = (
                update(project_git_configs_table)
                .where(project_git_configs_table.c.project_id == project_id)
                .values(
                    git_repo_url=git_repo_url,
                    git_branch=git_branch,
                    git_access_token_encrypted=git_access_token_encrypted,
                    features_root=features_root,
                )
            )
        try:
            await self._session.execute(stmt)
        except ProgrammingError as exc:
            if not self._is_legacy_features_root_error(exc):
                raise
            await self._session.rollback()
            await self._session.execute(
                self._legacy_git_config_upsert(
                    project_id=project_id,
                    existing=existing is not None,
                    git_repo_url=git_repo_url,
                    git_branch=git_branch,
                    git_access_token_encrypted=git_access_token_encrypted,
                )
            )
            return await self._get_git_config_via_legacy_schema(project_id)
        return await self.get_git_config(project_id)

    @staticmethod
    def _to_project(row: Mapping[Any, Any]) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _to_git_config(row: Mapping[Any, Any]) -> ProjectGitConfig:
        return ProjectGitConfig(
            project_id=row["project_id"],
            git_repo_url=row["git_repo_url"],
            git_branch=row["git_branch"],
            git_access_token_encrypted=row["git_access_token_encrypted"],
            features_root=row.get("features_root") or "features/",
        )

    @staticmethod
    def _legacy_git_config_select(project_id: UUID) -> Select:
        return select(
            project_git_configs_table.c.id,
            project_git_configs_table.c.project_id,
            project_git_configs_table.c.git_repo_url,
            project_git_configs_table.c.git_branch,
            project_git_configs_table.c.git_access_token_encrypted,
        ).where(project_git_configs_table.c.project_id == project_id)

    @staticmethod
    def _legacy_git_config_upsert(
        *,
        project_id: UUID,
        existing: bool,
        git_repo_url: str,
        git_branch: str,
        git_access_token_encrypted: bytes,
    ) -> Any:
        if not existing:
            return insert(project_git_configs_table).values(
                id=uuid4(),
                project_id=project_id,
                git_repo_url=git_repo_url,
                git_branch=git_branch,
                git_access_token_encrypted=git_access_token_encrypted,
            )
        return (
            update(project_git_configs_table)
            .where(project_git_configs_table.c.project_id == project_id)
            .values(
                git_repo_url=git_repo_url,
                git_branch=git_branch,
                git_access_token_encrypted=git_access_token_encrypted,
            )
        )

    async def _get_git_config_via_legacy_schema(
        self,
        project_id: UUID,
    ) -> ProjectGitConfig | None:
        row = (
            await self._session.execute(self._legacy_git_config_select(project_id))
        ).mappings().one_or_none()
        if row is None:
            return None
        return self._to_git_config(row)

    @staticmethod
    def _is_legacy_features_root_error(exc: ProgrammingError) -> bool:
        message = str(exc.orig).lower()
        statement = (exc.statement or "").lower()
        return "features_root" in message or "features_root" in statement
