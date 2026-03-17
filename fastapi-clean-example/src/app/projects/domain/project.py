from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class Project:
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class ProjectGitConfig:
    project_id: UUID
    git_repo_url: str
    git_branch: str
    git_access_token_encrypted: bytes
    features_root: str
