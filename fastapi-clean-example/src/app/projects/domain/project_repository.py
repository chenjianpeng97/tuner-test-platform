from typing import Protocol
from uuid import UUID

from app.projects.domain.project import Project, ProjectGitConfig


class ProjectRepository(Protocol):
    async def list_projects(self) -> list[Project]: ...

    async def get_project(self, project_id: UUID) -> Project | None: ...

    async def create_project(
        self,
        *,
        name: str,
        description: str | None,
    ) -> Project: ...

    async def update_project(
        self,
        *,
        project_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project | None: ...

    async def delete_project(self, project_id: UUID) -> bool: ...

    async def get_git_config(self, project_id: UUID) -> ProjectGitConfig | None: ...

    async def upsert_git_config(
        self,
        *,
        project_id: UUID,
        git_repo_url: str,
        git_branch: str,
        git_access_token_encrypted: bytes,
        features_root: str,
    ) -> ProjectGitConfig | None: ...
