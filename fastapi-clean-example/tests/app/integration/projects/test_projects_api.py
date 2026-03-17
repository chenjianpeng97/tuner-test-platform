from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
import tempfile
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from dishka import Provider, Scope, provide
from fastapi.testclient import TestClient

from app.bdd.features.domain.feature_repository import FeatureSyncSummary
from app.bdd.features.domain.feature_sync_service import (
    FeatureSyncError,
    FeatureSyncService,
)
from app.bdd.features.gateway.sqlalchemy_feature_repo import SqlalchemyFeatureRepository
from app.infrastructure.adapters.types import MainAsyncSession
from app.projects.domain.project import Project, ProjectGitConfig
from app.projects.gateway.sqlalchemy_project_repo import SqlalchemyProjectRepository
from app.run import make_app
from app.setup.config.settings import load_settings


class _FakeSession:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class _TestMainSessionProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def provide_main_session(self) -> AsyncIterator[MainAsyncSession]:
        yield cast(MainAsyncSession, _FakeSession())


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    app = make_app(_TestMainSessionProvider(), settings=load_settings(env="local"))
    with TestClient(app) as test_client:
        yield test_client


def _project(
    *,
    project_id: UUID | None = None,
    name: str = "demo-project",
    description: str | None = "demo description",
) -> Project:
    now = datetime.now(tz=UTC)
    return Project(
        id=project_id or uuid4(),
        name=name,
        description=description,
        created_at=now,
        updated_at=now,
    )


def _git_config(*, project_id: UUID) -> ProjectGitConfig:
    return ProjectGitConfig(
        project_id=project_id,
        git_repo_url="https://github.com/example/repo.git",
        git_branch="main",
        git_access_token_encrypted=b"encrypted-token",
        features_root="features/",
    )


def _feature_row(*, project_id: UUID, feature_id: UUID, file_path: str) -> dict[str, str]:
    return {
        "id": feature_id,
        "project_id": project_id,
        "file_path": file_path,
        "feature_name": "Demo Feature",
        "content": "Feature: Demo",
        "git_sha": None,
    }


def test_list_projects_returns_rows(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _project()
    list_projects_mock = AsyncMock(return_value=[row])
    monkeypatch.setattr(
        SqlalchemyProjectRepository, "list_projects", list_projects_mock
    )

    response = client.get("/api/v1/projects/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(row.id)
    assert payload[0]["name"] == row.name


def test_get_project_returns_404_when_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_project_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)

    response = client.get(f"/api/v1/projects/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_project_returns_201(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _project(name="created-project")
    create_project_mock = AsyncMock(return_value=row)
    monkeypatch.setattr(
        SqlalchemyProjectRepository,
        "create_project",
        create_project_mock,
    )

    response = client.post(
        "/api/v1/projects/",
        json={
            "name": "created-project",
            "description": "created in test",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == str(row.id)
    assert payload["name"] == row.name
    assert create_project_mock.await_count == 1
    assert create_project_mock.await_args.kwargs["name"] == "created-project"
    assert create_project_mock.await_args.kwargs["description"] == "created in test"


def test_update_project_returns_updated_project(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    updated = _project(
        project_id=project_id,
        name="updated-project",
        description="updated description",
    )

    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    update_project_mock = AsyncMock(return_value=updated)

    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)
    monkeypatch.setattr(
        SqlalchemyProjectRepository,
        "update_project",
        update_project_mock,
    )

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "updated-project",
            "description": "updated description",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(updated.id)
    assert payload["name"] == "updated-project"
    assert update_project_mock.await_count == 1
    assert update_project_mock.await_args.kwargs["project_id"] == project_id
    assert update_project_mock.await_args.kwargs["name"] == "updated-project"
    assert update_project_mock.await_args.kwargs["description"] == "updated description"


def test_upsert_git_config_does_not_return_pat(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()

    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    upsert_git_config_mock = AsyncMock(return_value=_git_config(project_id=project_id))

    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)
    monkeypatch.setattr(
        SqlalchemyProjectRepository,
        "upsert_git_config",
        upsert_git_config_mock,
    )

    response = client.put(
        f"/api/v1/projects/{project_id}/git-config",
        json={
            "git_repo_url": "https://github.com/example/repo.git",
            "git_branch": "main",
            "git_access_token": "plain-pat",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == str(project_id)
    assert payload["git_repo_url"] == "https://github.com/example/repo.git"
    assert "git_access_token" not in payload
    assert upsert_git_config_mock.await_count == 1
    assert upsert_git_config_mock.await_args.kwargs["project_id"] == project_id


def test_import_junit_invalid_xml_returns_422(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)

    response = client.post(
        f"/api/v1/projects/{project_id}/test-runs/import",
        files={"file": ("results.xml", b"<invalid", "application/xml")},
    )

    assert response.status_code == 422


def test_import_junit_success(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)

    create_test_run_mock = AsyncMock(return_value=uuid4())
    insert_results_mock = AsyncMock(return_value=None)
    find_scenario_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "app.bdd.coverage.gateway.sqlalchemy_coverage_repo.SqlalchemyCoverageRepository.create_completed_test_run",
        create_test_run_mock,
    )
    monkeypatch.setattr(
        "app.bdd.coverage.gateway.sqlalchemy_coverage_repo.SqlalchemyCoverageRepository.insert_test_run_results",
        insert_results_mock,
    )
    monkeypatch.setattr(
        "app.bdd.coverage.gateway.sqlalchemy_coverage_repo.SqlalchemyCoverageRepository.find_scenario_id",
        find_scenario_mock,
    )

    xml = (
        "<?xml version=\"1.0\"?><testsuite>"
        "<testcase classname=\"auth.feature\" name=\"Login success\" time=\"0.1\"/>"
        "<testcase classname=\"auth.feature\" name=\"Login fail\" time=\"0.2\">"
        "<failure message=\"boom\">trace</failure></testcase>"
        "</testsuite>"
    ).encode("utf-8")

    response = client.post(
        f"/api/v1/projects/{project_id}/test-runs/import",
        files={"file": ("results.xml", xml, "application/xml")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["passed"] == 1
    assert payload["failed"] == 1


def test_create_feature_conflict_returns_409(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    feature_id = uuid4()
    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)

    existing_feature = _feature_row(
        project_id=project_id,
        feature_id=feature_id,
        file_path="auth.feature",
    )
    get_feature_by_path_mock = AsyncMock(return_value=existing_feature)
    monkeypatch.setattr(
        SqlalchemyFeatureRepository,
        "get_feature_by_path",
        get_feature_by_path_mock,
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/features",
        json={
            "file_path": "auth.feature",
            "content": "Feature: Auth",
        },
    )

    assert response.status_code == 409


def test_update_feature_git_failure_returns_502(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    feature_id = uuid4()
    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)

    feature = _feature_row(
        project_id=project_id,
        feature_id=feature_id,
        file_path="auth.feature",
    )
    get_feature_mock = AsyncMock(return_value=feature)
    monkeypatch.setattr(
        SqlalchemyFeatureRepository, "get_feature_by_project", get_feature_mock
    )

    git_config_mock = AsyncMock(return_value=_git_config(project_id=project_id))
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_git_config", git_config_mock)

    replace_features_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        SqlalchemyFeatureRepository, "replace_project_features", replace_features_mock
    )

    monkeypatch.setattr(
        "app.projects.api.router.FeatureSyncService._collect_feature_files",
        lambda *_args, **_kwargs: [],
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        monkeypatch.setattr(
            "app.projects.api.router._prepare_checkout_dir",
            lambda **_kwargs: repo_dir,
        )
        monkeypatch.setattr(
            "app.projects.gateway.git_sync_service.GitSyncService.add",
            lambda *_args, **_kwargs: None,
        )
        monkeypatch.setattr(
            "app.projects.gateway.git_sync_service.GitSyncService.commit",
            lambda *_args, **_kwargs: None,
        )
        monkeypatch.setattr(
            "app.projects.gateway.git_sync_service.GitSyncService.push",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("push failed")),
        )

        response = client.put(
            f"/api/v1/projects/{project_id}/features/{feature_id}",
            json={
                "content": "Feature: Auth",
                "commit_message": "chore: update auth.feature",
            },
        )

    assert response.status_code == 502
    assert git_config_mock.await_count == 1


def test_get_git_config_returns_404_when_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()

    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    get_git_config_mock = AsyncMock(return_value=None)

    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)
    monkeypatch.setattr(
        SqlalchemyProjectRepository,
        "get_git_config",
        get_git_config_mock,
    )

    response = client.get(f"/api/v1/projects/{project_id}/git-config")

    assert response.status_code == 404
    assert response.json()["detail"] == "Git config not found"
    assert get_git_config_mock.await_count == 1


def test_create_project_returns_422_when_name_is_empty(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects/",
        json={
            "name": "",
            "description": "bad request",
        },
    )

    assert response.status_code == 422


def test_update_project_returns_422_when_name_is_empty(
    client: TestClient,
) -> None:
    response = client.patch(
        f"/api/v1/projects/{uuid4()}",
        json={
            "name": "",
        },
    )

    assert response.status_code == 422


def test_upsert_git_config_returns_422_when_token_is_empty(
    client: TestClient,
) -> None:
    response = client.put(
        f"/api/v1/projects/{uuid4()}/git-config",
        json={
            "git_repo_url": "https://github.com/example/repo.git",
            "git_branch": "main",
            "git_access_token": "",
        },
    )

    assert response.status_code == 422


def test_get_project_returns_422_when_project_id_is_invalid(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/projects/not-a-uuid")

    assert response.status_code == 422


def test_delete_project_returns_404_when_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_project_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)

    response = client.delete(f"/api/v1/projects/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_sync_project_features_returns_summary(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synced_at = datetime.now(tz=UTC)
    sync_mock = AsyncMock(
        return_value=FeatureSyncSummary(
            added=2,
            updated=1,
            deleted=0,
            total=3,
            synced_at=synced_at,
        )
    )
    monkeypatch.setattr(FeatureSyncService, "sync_project_features", sync_mock)

    response = client.post(f"/api/v1/projects/{uuid4()}/sync")

    assert response.status_code == 200
    payload = response.json()
    assert payload["added"] == 2
    assert payload["updated"] == 1
    assert payload["deleted"] == 0
    assert payload["total"] == 3


def test_sync_project_features_returns_502_on_git_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_mock = AsyncMock(side_effect=FeatureSyncError("auth failed"))
    monkeypatch.setattr(FeatureSyncService, "sync_project_features", sync_mock)

    response = client.post(f"/api/v1/projects/{uuid4()}/sync")

    assert response.status_code == 502
    assert response.json()["detail"] == "Git sync failed: auth failed"


def test_list_project_features_returns_tree(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    root_feature_id = uuid4()
    child_feature_id = uuid4()

    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    list_features_mock = AsyncMock(
        return_value=[
            {
                "id": root_feature_id,
                "project_id": project_id,
                "file_path": "features/user.feature",
                "feature_name": "User",
                "parent_feature_id": None,
                "depth": 0,
            },
            {
                "id": child_feature_id,
                "project_id": project_id,
                "file_path": "features/user/user_auth.feature",
                "feature_name": "User Auth",
                "parent_feature_id": root_feature_id,
                "depth": 1,
            },
        ]
    )
    list_scenarios_mock = AsyncMock(
        return_value=[
            {
                "id": uuid4(),
                "feature_id": root_feature_id,
                "scenario_name": "Create user",
                "rule_name": None,
                "line_number": 10,
            },
            {
                "id": uuid4(),
                "feature_id": child_feature_id,
                "scenario_name": "Admin can auth",
                "rule_name": "Authorization",
                "line_number": 22,
            },
        ]
    )

    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)
    monkeypatch.setattr(
        SqlalchemyFeatureRepository,
        "list_features_by_project",
        list_features_mock,
    )
    monkeypatch.setattr(
        SqlalchemyFeatureRepository,
        "list_scenarios_by_project",
        list_scenarios_mock,
    )
    monkeypatch.setattr(
        "app.bdd.coverage.gateway.sqlalchemy_coverage_repo.SqlalchemyCoverageRepository.list_latest_scenario_status",
        AsyncMock(return_value={}),
    )

    response = client.get(f"/api/v1/projects/{project_id}/features")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(root_feature_id)
    assert payload[0]["scenario_count"] == 1
    assert len(payload[0]["scenarios"]) == 1
    assert payload[0]["scenarios"][0]["name"] == "Create user"

    assert len(payload[0]["children"]) == 1
    child = payload[0]["children"][0]
    assert child["id"] == str(child_feature_id)
    assert child["scenario_count"] == 1
    assert len(child["rules"]) == 1
    assert child["rules"][0]["name"] == "Authorization"
    assert child["rules"][0]["scenarios"][0]["name"] == "Admin can auth"


def test_get_feature_detail_returns_content(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()
    feature_id = uuid4()

    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    get_feature_mock = AsyncMock(
        return_value={
            "id": feature_id,
            "project_id": project_id,
            "file_path": "features/user.feature",
            "feature_name": "User",
            "content": "Feature: User\n  Scenario: Login",
            "git_sha": "abc123",
        }
    )

    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)
    monkeypatch.setattr(
        SqlalchemyFeatureRepository,
        "get_feature_by_project",
        get_feature_mock,
    )

    response = client.get(f"/api/v1/projects/{project_id}/features/{feature_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(feature_id)
    assert payload["project_id"] == str(project_id)
    assert payload["feature_name"] == "User"
    assert payload["content"] == "Feature: User\n  Scenario: Login"


def test_get_feature_detail_returns_404_when_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid4()

    get_project_mock = AsyncMock(return_value=_project(project_id=project_id))
    get_feature_mock = AsyncMock(return_value=None)

    monkeypatch.setattr(SqlalchemyProjectRepository, "get_project", get_project_mock)
    monkeypatch.setattr(
        SqlalchemyFeatureRepository,
        "get_feature_by_project",
        get_feature_mock,
    )

    response = client.get(f"/api/v1/projects/{project_id}/features/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Feature not found"
