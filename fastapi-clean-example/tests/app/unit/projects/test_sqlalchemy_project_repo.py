import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.exc import ProgrammingError

from app.projects.domain.project import Project, ProjectGitConfig
from app.projects.gateway.sqlalchemy_project_repo import SqlalchemyProjectRepository


class _FakeResult:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def mappings(self) -> "_FakeResult":
        return self

    def one_or_none(self) -> dict | None:
        return self._row


class _FakeSession:
    def __init__(self, responses: Sequence[object]) -> None:
        self._responses = list(responses)
        self.executed_statements: list[object] = []
        self.rollback_count = 0

    async def execute(self, stmt: object) -> _FakeResult:
        self.executed_statements.append(stmt)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def rollback(self) -> None:
        self.rollback_count += 1


def _legacy_features_root_error() -> ProgrammingError:
    return ProgrammingError(
        statement='SELECT project_git_configs.features_root FROM project_git_configs',
        params={},
        orig=Exception('column "features_root" does not exist'),
    )


def test_get_git_config_falls_back_for_legacy_schema() -> None:
    project_id = uuid4()
    session = _FakeSession(
        [
            _legacy_features_root_error(),
            _FakeResult(
                {
                    "project_id": project_id,
                    "git_repo_url": "https://github.com/example/repo.git",
                    "git_branch": "main",
                    "git_access_token_encrypted": b"secret",
                }
            ),
        ]
    )

    repo = SqlalchemyProjectRepository(SimpleNamespace(  # type: ignore[arg-type]
        execute=session.execute,
        rollback=session.rollback,
    ))

    config = asyncio.run(repo.get_git_config(project_id))

    assert config == ProjectGitConfig(
        project_id=project_id,
        git_repo_url="https://github.com/example/repo.git",
        git_branch="main",
        git_access_token_encrypted=b"secret",
        features_root="features/",
    )
    assert session.rollback_count == 1
    assert "features_root" in str(session.executed_statements[0])
    assert "features_root" not in str(session.executed_statements[1])


def test_upsert_git_config_falls_back_for_legacy_schema() -> None:
    project_id = uuid4()
    now = datetime.now(tz=UTC)
    session = _FakeSession(
        [
            _FakeResult(
                {
                    "id": project_id,
                    "name": "demo",
                    "description": None,
                    "created_at": now,
                    "updated_at": now,
                }
            ),
            _legacy_features_root_error(),
            _FakeResult(None),
            _legacy_features_root_error(),
            _FakeResult(None),
            _FakeResult(
                {
                    "project_id": project_id,
                    "git_repo_url": "https://github.com/example/repo.git",
                    "git_branch": "main",
                    "git_access_token_encrypted": b"secret",
                }
            ),
        ]
    )
    repo = SqlalchemyProjectRepository(SimpleNamespace(  # type: ignore[arg-type]
        execute=session.execute,
        rollback=session.rollback,
    ))

    config = asyncio.run(
        repo.upsert_git_config(
            project_id=project_id,
            git_repo_url="https://github.com/example/repo.git",
            git_branch="main",
            git_access_token_encrypted=b"secret",
            features_root="custom/features/",
        )
    )

    assert config == ProjectGitConfig(
        project_id=project_id,
        git_repo_url="https://github.com/example/repo.git",
        git_branch="main",
        git_access_token_encrypted=b"secret",
        features_root="features/",
    )
    assert session.rollback_count == 2
    assert "features_root" in str(session.executed_statements[1])
    assert "features_root" not in str(session.executed_statements[2])
    assert "features_root" in str(session.executed_statements[3])
    assert "features_root" not in str(session.executed_statements[4])
    assert "features_root" not in str(session.executed_statements[5])
