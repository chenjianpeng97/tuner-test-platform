import base64
import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bdd.features.domain.feature_sync_service import (
    FeatureSyncError,
    FeatureSyncService,
    GitConfigNotFoundError,
    ProjectNotFoundError,
)
from app.bdd.features.gateway.gherkin_parser import GherkinFeatureParser
from app.bdd.features.gateway.sqlalchemy_feature_repo import SqlalchemyFeatureRepository
from app.bdd.coverage.gateway.sqlalchemy_coverage_repo import (
    SqlalchemyCoverageRepository,
    TestRunResultSpec,
)
from app.bdd.coverage.gateway.junit_parser import JunitParseError, parse_junit_results
from app.bdd.execution.domain.behave_runner import (
    BehaveRunner,
    make_done_event,
    stream_log_queue,
)
from app.bdd.execution.gateway.sqlalchemy_execution_repo import (
    SqlalchemyExecutionRepository,
)
from app.bdd.execution.gateway.sqlalchemy_hybrid_repo import (
    SqlalchemyHybridRepository,
)
from app.bdd.execution.gateway.sqlalchemy_execution_helpers import (
    ExecutionLookupRepository,
)
from app.bdd.execution.domain.hybrid_execution_service import HybridExecutionService
from app.bdd.execution.domain.step_auto_policy import StepAutoPolicy
from app.bdd.test_plans.gateway.sqlalchemy_test_plan_repo import (
    SqlalchemyTestPlanRepository,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.projects.api.schemas import (
    CoverageSummaryResponse,
    FeatureCreateRequest,
    FeatureDetailResponse,
    FeatureTreeNode,
    FeatureTreeRuleNode,
    FeatureTreeScenarioNode,
    FeatureUpdateRequest,
    GitConfigResponse,
    GitConfigUpsertRequest,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectSyncResponse,
    ProjectUpdateRequest,
    StepSuggestionItem,
    SubFeatureCreateRequest,
    TestRunImportResponse,
    TestPlanBulkAddRequest,
    TestPlanBulkAddResponse,
    TestPlanCreateRequest,
    TestPlanItemResponse,
    TestPlanItemStatusUpdateRequest,
    TestPlanProgressResponse,
    TestPlanResponse,
    TestPlanSyncRequest,
    TestPlanSyncResponse,
    TestPlanUpdateRequest,
    TestRunCreateRequest,
    TestRunResponse,
    ScenarioExecutionCreateRequest,
    ScenarioExecutionResponse,
    StepExecutionRecordResponse,
    StepManualUpdateRequest,
    StepAutoExecuteRequest,
    ScenarioExecutionStatusResponse,
)
from app.projects.gateway.git_sync_service import GitSyncService
from app.projects.gateway.sqlalchemy_project_repo import SqlalchemyProjectRepository

router = APIRouter(prefix="/projects", tags=["Projects"])


def _get_repo(
    session: FromDishka[MainAsyncSession],
) -> SqlalchemyProjectRepository:
    return SqlalchemyProjectRepository(session)


async def _ensure_project_exists(
    *,
    repo: SqlalchemyProjectRepository,
    project_id: UUID,
) -> None:
    if await repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")


def _resolve_repo_url(*, repo_url: str, token: str | None) -> str:
    return FeatureSyncService._inject_pat(repo_url, token)


def _decode_token(encoded: bytes) -> str | None:
    return FeatureSyncService._decode_token(encoded)


def _default_commit_message(file_path: str) -> str:
    return f"chore: update {file_path}"


def _default_create_commit_message(file_path: str) -> str:
    return f"chore: add {file_path}"


def _derive_sub_feature_path(parent_path: str, child_name: str) -> str:
    parent = Path(parent_path)
    parent_dir = parent.parent / parent.stem
    return (parent_dir / f"{child_name}.feature").as_posix()


def _map_coverage_status(value: str | None) -> str:
    if value == "pass":
        return "covered"
    if value == "fail":
        return "failed"
    return "uncovered"


def _parse_junit_payload(payload: bytes) -> list[TestRunResultSpec]:
    try:
        cases = parse_junit_results(payload)
    except JunitParseError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid XML: {exc}") from exc

    return [
        TestRunResultSpec(
            feature_name=case.feature_name,
            scenario_name=case.scenario_name,
            status=case.status,
            duration_seconds=case.duration_seconds,
            error_message=case.error_message,
            stack_trace=case.stack_trace,
            scenario_id=None,
        )
        for case in cases
    ]


def _plan_response(row: dict[str, Any]) -> TestPlanResponse:
    return TestPlanResponse(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row.get("description"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _plan_item_response(row: dict[str, Any]) -> TestPlanItemResponse:
    return TestPlanItemResponse(
        id=row["id"],
        test_plan_id=row["test_plan_id"],
        scenario_id=row["scenario_id"],
        status=row["status"],
        notes=row.get("notes"),
        updated_at=row["updated_at"],
    )


def _test_run_response(row: dict[str, Any]) -> TestRunResponse:
    return TestRunResponse(
        id=row["id"],
        project_id=row["project_id"],
        status=row["status"],
        scope_type=row["scope_type"],
        scope_value=row.get("scope_value"),
        triggered_at=row["triggered_at"],
        completed_at=row.get("completed_at"),
    )


def _build_step_record_response(
    row: dict[str, Any],
    available_stages: list[str],
) -> StepExecutionRecordResponse:
    return StepExecutionRecordResponse(
        id=row["id"],
        step_id=row["step_id"],
        step_order=row["step_order"],
        keyword=row.get("keyword") or "",
        text=row.get("text") or "",
        execution_mode=row.get("execution_mode") or "auto",
        status=row.get("status") or "pending",
        stage_id=row.get("stage_id"),
        executor=row.get("executor"),
        executed_at=row.get("executed_at"),
        notes=row.get("notes"),
        error_message=row.get("error_message"),
        available_stages=available_stages,
    )


def _checkout_root() -> Path:
    return Path.cwd() / ".cache" / "bdd-project-sync"


def _prepare_checkout_dir(
    *,
    project_id: UUID,
    git_repo_url: str,
    git_branch: str,
    git_access_token_encrypted: bytes,
    git_sync: GitSyncService,
) -> Path:
    checkout_root = _checkout_root()
    checkout_dir = checkout_root / str(project_id)
    checkout_root.mkdir(parents=True, exist_ok=True)

    token = _decode_token(git_access_token_encrypted)
    repo_url = _resolve_repo_url(repo_url=git_repo_url, token=token)

    try:
        git_dir = checkout_dir / ".git"
        if git_dir.exists():
            git_sync.pull(repo_path=checkout_dir)
        else:
            git_sync.clone(
                repo_url=repo_url,
                branch=git_branch,
                dst_path=checkout_dir,
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Git sync failed: {exc}") from exc

    return checkout_dir


async def _run_behave_background(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    project_id: UUID,
    test_run_id: UUID,
    behave_work_dir: Path,
    scope_type: str,
    scope_value: str | None,
    executor_config: dict[str, Any] | None,
) -> None:
    async with session_factory() as session:
        execution_repo = SqlalchemyExecutionRepository(session)
        coverage_repo = SqlalchemyCoverageRepository(session)
        runner = BehaveRunner(
            session=session,
            execution_repo=execution_repo,
            coverage_repo=coverage_repo,
            log_root=Path.cwd() / ".cache" / "bdd-test-runs",
        )
        await runner.run(
            project_id=project_id,
            test_run_id=test_run_id,
            behave_work_dir=behave_work_dir,
            scope_type=scope_type,
            scope_value=scope_value,
            executor_config=executor_config,
        )


@router.get("/", response_model=list[ProjectResponse])
@inject
async def list_projects(
    session: FromDishka[MainAsyncSession],
) -> list[ProjectResponse]:
    repo = _get_repo(session)
    rows = await repo.list_projects()
    return [ProjectResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_project(
    request: ProjectCreateRequest,
    session: FromDishka[MainAsyncSession],
) -> ProjectResponse:
    repo = _get_repo(session)
    row = await repo.create_project(name=request.name, description=request.description)
    await session.commit()
    return ProjectResponse.model_validate(row, from_attributes=True)


@router.get("/{project_id}", response_model=ProjectResponse)
@inject
async def get_project(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> ProjectResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)
    row = await repo.get_project(project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(row, from_attributes=True)


@router.patch("/{project_id}", response_model=ProjectResponse)
@inject
async def update_project(
    project_id: UUID,
    request: ProjectUpdateRequest,
    session: FromDishka[MainAsyncSession],
) -> ProjectResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)
    row = await repo.update_project(
        project_id=project_id,
        name=request.name,
        description=request.description,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.commit()
    return ProjectResponse.model_validate(row, from_attributes=True)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_project(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> None:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)
    deleted = await repo.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.commit()


@router.get("/{project_id}/git-config", response_model=GitConfigResponse)
@inject
async def get_git_config(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> GitConfigResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)
    config = await repo.get_git_config(project_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Git config not found")
    return GitConfigResponse(
        project_id=config.project_id,
        git_repo_url=config.git_repo_url,
        git_branch=config.git_branch,
        features_root=config.features_root,
    )


@router.put("/{project_id}/git-config", response_model=GitConfigResponse)
@inject
async def upsert_git_config(
    project_id: UUID,
    request: GitConfigUpsertRequest,
    session: FromDishka[MainAsyncSession],
) -> GitConfigResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)
    encrypted = base64.b64encode(request.git_access_token.encode("utf-8"))
    features_root = request.features_root.strip()
    if not features_root:
        features_root = "features/"
    config = await repo.upsert_git_config(
        project_id=project_id,
        git_repo_url=request.git_repo_url,
        git_branch=request.git_branch,
        git_access_token_encrypted=encrypted,
        features_root=features_root,
    )
    if config is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.commit()
    return GitConfigResponse(
        project_id=config.project_id,
        git_repo_url=config.git_repo_url,
        git_branch=config.git_branch,
        features_root=config.features_root,
    )


def _build_feature_tree(
    *,
    feature_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    coverage_status: dict[UUID, str],
) -> list[FeatureTreeNode]:
    ordered_ids: list[UUID] = []
    parent_by_id: dict[UUID, UUID | None] = {}
    payload_by_id: dict[UUID, dict[str, Any]] = {}

    for row in feature_rows:
        feature_id = row["id"]
        if not isinstance(feature_id, UUID):
            continue
        ordered_ids.append(feature_id)
        parent_by_id[feature_id] = row.get("parent_feature_id")
        payload_by_id[feature_id] = {
            "type": "feature",
            "id": feature_id,
            "file_path": row["file_path"],
            "feature_name": row["feature_name"],
            "depth": row["depth"],
            "scenario_count": 0,
            "rules": [],
            "scenarios": [],
            "children": [],
        }

    rules_by_feature: dict[UUID, dict[str, list[FeatureTreeScenarioNode]]] = {}

    for row in scenario_rows:
        feature_id = row.get("feature_id")
        if not isinstance(feature_id, UUID) or feature_id not in payload_by_id:
            continue

        scenario = FeatureTreeScenarioNode(
            id=row["id"],
            name=row["scenario_name"],
            rule_name=row.get("rule_name"),
            line_number=row.get("line_number"),
            coverage_status=_map_coverage_status(
                coverage_status.get(row["id"], "uncovered")
            ),
        )
        payload_by_id[feature_id]["scenario_count"] += 1

        rule_name = scenario.rule_name
        if isinstance(rule_name, str) and len(rule_name) > 0:
            feature_rules = rules_by_feature.setdefault(feature_id, {})
            feature_rules.setdefault(rule_name, []).append(scenario)
            continue

        payload_by_id[feature_id]["scenarios"].append(scenario)

    for feature_id, grouped_rules in rules_by_feature.items():
        payload_by_id[feature_id]["rules"] = [
            FeatureTreeRuleNode(name=name, scenarios=scenarios)
            for name, scenarios in grouped_rules.items()
        ]

    root_nodes: list[dict[str, Any]] = []
    for feature_id in ordered_ids:
        payload = payload_by_id[feature_id]
        parent_id = parent_by_id[feature_id]
        if isinstance(parent_id, UUID) and parent_id in payload_by_id:
            payload_by_id[parent_id]["children"].append(payload)
            continue
        root_nodes.append(payload)

    return [FeatureTreeNode.model_validate(node) for node in root_nodes]


def _to_utf8_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""


@router.get("/{project_id}/features", response_model=list[FeatureTreeNode])
@inject
async def list_project_features(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> list[FeatureTreeNode]:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    features_repo = SqlalchemyFeatureRepository(session)
    feature_rows = await features_repo.list_features_by_project(project_id=project_id)
    scenario_rows = await features_repo.list_scenarios_by_project(project_id=project_id)
    coverage_repo = SqlalchemyCoverageRepository(session)
    coverage_status = await coverage_repo.list_latest_scenario_status(
        project_id=project_id
    )

    return _build_feature_tree(
        feature_rows=[dict(row) for row in feature_rows],
        scenario_rows=[dict(row) for row in scenario_rows],
        coverage_status=coverage_status,
    )


@router.get("/{project_id}/steps/suggest", response_model=list[StepSuggestionItem])
@inject
async def suggest_steps(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
    q: str = Query(default="", max_length=200),
) -> list[StepSuggestionItem]:
    if not q.strip():
        return []

    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    features_repo = SqlalchemyFeatureRepository(session)
    rows = await features_repo.suggest_steps(project_id=project_id, prefix=q.strip())
    return [StepSuggestionItem(keyword=row["keyword"], text=row["text"]) for row in rows]


@router.post(
    "/{project_id}/test-runs/import",
    response_model=TestRunImportResponse,
)
@inject
async def import_junit_results(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
    file: UploadFile = File(...),
) -> TestRunImportResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    payload = await file.read()
    parsed = _parse_junit_payload(payload)

    coverage_repo = SqlalchemyCoverageRepository(session)
    test_run_id = await coverage_repo.create_completed_test_run(
        project_id=project_id,
        scope_type="import",
        scope_value="junit",
    )

    results: list[TestRunResultSpec] = []
    for item in parsed:
        scenario_id = await coverage_repo.find_scenario_id(
            project_id=project_id,
            feature_name=item.feature_name,
            scenario_name=item.scenario_name,
        )
        results.append(
            TestRunResultSpec(
                feature_name=item.feature_name,
                scenario_name=item.scenario_name,
                status=item.status,
                duration_seconds=item.duration_seconds,
                error_message=item.error_message,
                stack_trace=item.stack_trace,
                scenario_id=scenario_id,
            )
        )

    await coverage_repo.insert_test_run_results(
        test_run_id=test_run_id,
        results=results,
    )
    await session.commit()

    summary = {"pass": 0, "fail": 0, "skip": 0}
    for item in results:
        if item.status in summary:
            summary[item.status] += 1

    return TestRunImportResponse(
        test_run_id=test_run_id,
        status="completed",
        total=len(results),
        passed=summary["pass"],
        failed=summary["fail"],
        skipped=summary["skip"],
    )


@router.get("/{project_id}/coverage", response_model=CoverageSummaryResponse)
@inject
async def get_project_coverage_summary(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> CoverageSummaryResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    coverage_repo = SqlalchemyCoverageRepository(session)
    summary = await coverage_repo.get_project_coverage_summary(project_id=project_id)
    return CoverageSummaryResponse(**summary)


@router.post(
    "/{project_id}/test-runs",
    response_model=TestRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def trigger_test_run(
    project_id: UUID,
    request: TestRunCreateRequest,
    session: FromDishka[MainAsyncSession],
    session_factory: FromDishka[async_sessionmaker[AsyncSession]],
) -> TestRunResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    execution_repo = SqlalchemyExecutionRepository(session)
    if await execution_repo.has_running_test_run(project_id=project_id):
        raise HTTPException(status_code=409, detail="Test run already running")

    behave_config = await execution_repo.get_behave_config(project_id=project_id)
    if behave_config is None:
        raise HTTPException(status_code=404, detail="Behave config not found")

    behave_work_dir = Path(behave_config["behave_work_dir"])
    pending = await execution_repo.create_pending_test_run(
        project_id=project_id,
        scope_type=request.scope_type,
        scope_value=request.scope_value,
        executor_config=request.executor_config,
    )
    test_run_id = pending["id"]

    if not behave_work_dir.exists():
        await execution_repo.update_test_run_status(
            test_run_id=test_run_id,
            status="failed",
            completed_at=datetime.now(tz=UTC),
        )
        await session.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Behave work dir not found: {behave_work_dir}",
        )

    await session.commit()

    asyncio.create_task(
        _run_behave_background(
            session_factory=session_factory,
            project_id=project_id,
            test_run_id=test_run_id,
            behave_work_dir=behave_work_dir,
            scope_type=request.scope_type,
            scope_value=request.scope_value,
            executor_config=request.executor_config,
        )
    )

    return _test_run_response(dict(pending))


async def _stream_log_file(path: Path) -> AsyncGenerator[str, None]:
    if not path.exists():
        yield make_done_event()
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            yield f"data: {line.rstrip()}\n\n"
    yield make_done_event()


async def _empty_sse() -> AsyncGenerator[str, None]:
    yield make_done_event()


@router.get("/{project_id}/test-runs/{test_run_id}/logs")
@inject
async def stream_test_run_logs(
    project_id: UUID,
    test_run_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> StreamingResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    execution_repo = SqlalchemyExecutionRepository(session)
    run = await execution_repo.get_test_run(
        project_id=project_id,
        test_run_id=test_run_id,
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Test run not found")

    status_value = run.get("status")
    log_path_value = run.get("log_path")
    log_path = Path(log_path_value) if isinstance(log_path_value, str) else None

    if status_value in {"completed", "failed"}:
        if log_path is None:
            return StreamingResponse(
                _empty_sse(),
                media_type="text/event-stream",
            )
        return StreamingResponse(
            _stream_log_file(log_path),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        stream_log_queue(test_run_id),
        media_type="text/event-stream",
    )


@router.get("/{project_id}/test-plans", response_model=list[TestPlanResponse])
@inject
async def list_test_plans(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> list[TestPlanResponse]:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    rows = await plans_repo.list_test_plans(project_id=project_id)
    return [_plan_response(dict(row)) for row in rows]


@router.post(
    "/{project_id}/test-plans",
    response_model=TestPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_test_plan(
    project_id: UUID,
    request: TestPlanCreateRequest,
    session: FromDishka[MainAsyncSession],
) -> TestPlanResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    row = await plans_repo.create_test_plan(
        project_id=project_id,
        name=request.name,
        description=request.description,
    )
    await session.commit()
    return _plan_response(dict(row))


@router.get("/{project_id}/test-plans/{plan_id}", response_model=TestPlanResponse)
@inject
async def get_test_plan(
    project_id: UUID,
    plan_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> TestPlanResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    row = await plans_repo.get_test_plan(project_id=project_id, plan_id=plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return _plan_response(dict(row))


@router.patch("/{project_id}/test-plans/{plan_id}", response_model=TestPlanResponse)
@inject
async def update_test_plan(
    project_id: UUID,
    plan_id: UUID,
    request: TestPlanUpdateRequest,
    session: FromDishka[MainAsyncSession],
) -> TestPlanResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    row = await plans_repo.update_test_plan(
        project_id=project_id,
        plan_id=plan_id,
        name=request.name,
        description=request.description,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Test plan not found")
    await session.commit()
    return _plan_response(dict(row))


@router.delete("/{project_id}/test-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_test_plan(
    project_id: UUID,
    plan_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> None:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    deleted = await plans_repo.delete_test_plan(project_id=project_id, plan_id=plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test plan not found")
    await session.commit()


@router.get(
    "/{project_id}/test-plans/{plan_id}/items",
    response_model=list[TestPlanItemResponse],
)
@inject
async def list_test_plan_items(
    project_id: UUID,
    plan_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> list[TestPlanItemResponse]:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    plan = await plans_repo.get_test_plan(project_id=project_id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")

    rows = await plans_repo.list_items(project_id=project_id, plan_id=plan_id)
    return [_plan_item_response(dict(row)) for row in rows]


@router.post(
    "/{project_id}/test-plans/{plan_id}/items",
    response_model=TestPlanBulkAddResponse,
)
@inject
async def add_test_plan_items(
    project_id: UUID,
    plan_id: UUID,
    request: TestPlanBulkAddRequest,
    session: FromDishka[MainAsyncSession],
) -> TestPlanBulkAddResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    plan = await plans_repo.get_test_plan(project_id=project_id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")

    result = await plans_repo.add_items(
        plan_id=plan_id,
        scenario_ids=request.scenario_ids,
    )
    await session.commit()
    return TestPlanBulkAddResponse(**result)


@router.patch(
    "/{project_id}/test-plans/{plan_id}/items/{item_id}",
    response_model=TestPlanItemResponse,
)
@inject
async def update_test_plan_item_status(
    project_id: UUID,
    plan_id: UUID,
    item_id: UUID,
    request: TestPlanItemStatusUpdateRequest,
    session: FromDishka[MainAsyncSession],
) -> TestPlanItemResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    plan = await plans_repo.get_test_plan(project_id=project_id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")

    item = await plans_repo.update_item_status(
        project_id=project_id,
        plan_id=plan_id,
        item_id=item_id,
        status=request.status,
        notes=request.notes,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Test plan item not found")
    await session.commit()
    return _plan_item_response(dict(item))


@router.get(
    "/{project_id}/test-plans/{plan_id}/progress",
    response_model=TestPlanProgressResponse,
)
@inject
async def get_test_plan_progress(
    project_id: UUID,
    plan_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> TestPlanProgressResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    plan = await plans_repo.get_test_plan(project_id=project_id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")

    summary = await plans_repo.get_progress(project_id=project_id, plan_id=plan_id)
    return TestPlanProgressResponse(
        total=summary["total"],
        not_run=summary["not_run"],
        pass_count=summary["pass"],
        fail_count=summary["fail"],
        skip_count=summary["skip"],
        blocked_count=summary["blocked"],
    )


@router.post(
    "/{project_id}/test-plans/{plan_id}/sync",
    response_model=TestPlanSyncResponse,
)
@inject
async def sync_test_plan_from_test_run(
    project_id: UUID,
    plan_id: UUID,
    request: TestPlanSyncRequest,
    session: FromDishka[MainAsyncSession],
) -> TestPlanSyncResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    plans_repo = SqlalchemyTestPlanRepository(session)
    plan = await plans_repo.get_test_plan(project_id=project_id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")

    result = await plans_repo.sync_items_from_test_run(
        project_id=project_id,
        plan_id=plan_id,
        test_run_id=request.test_run_id,
    )
    await session.commit()
    return TestPlanSyncResponse(**result)


@router.post(
    "/{project_id}/scenario-executions",
    response_model=ScenarioExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_scenario_execution(
    project_id: UUID,
    request: ScenarioExecutionCreateRequest,
    session: FromDishka[MainAsyncSession],
) -> ScenarioExecutionResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    hybrid_repo = SqlalchemyHybridRepository(session)
    execution_repo = SqlalchemyExecutionRepository(session)
    coverage_repo = SqlalchemyCoverageRepository(session)
    lookup_repo = ExecutionLookupRepository(session)
    service = HybridExecutionService(
        hybrid_repo=hybrid_repo,
        execution_repo=execution_repo,
        coverage_repo=coverage_repo,
        lookup_repo=lookup_repo,
        log_root=Path.cwd() / ".cache" / "bdd-hybrid",
        auto_policy=StepAutoPolicy(hybrid_repo),
    )
    try:
        result = await service.create_execution(
            project_id=project_id,
            scenario_id=request.scenario_id,
            test_plan_item_id=request.test_plan_item_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    execution = result["execution"]
    records = result["records"]
    available = result["available_stages"]
    steps = [
        _build_step_record_response(
            row,
            available.get(row["step_id"], []),
        )
        for row in records
    ]
    await session.commit()
    return ScenarioExecutionResponse(
        id=execution["id"],
        project_id=execution["project_id"],
        scenario_id=execution["scenario_id"],
        status=execution["status"],
        created_at=execution["created_at"],
        completed_at=execution.get("completed_at"),
        steps=steps,
    )


@router.get(
    "/{project_id}/scenario-executions/{exec_id}",
    response_model=ScenarioExecutionResponse,
)
@inject
async def get_scenario_execution(
    project_id: UUID,
    exec_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> ScenarioExecutionResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    hybrid_repo = SqlalchemyHybridRepository(session)
    execution = await hybrid_repo.get_scenario_execution(
        project_id=project_id, exec_id=exec_id
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Scenario execution not found")

    records = await hybrid_repo.list_execution_steps_with_text(exec_id=exec_id)
    available = await hybrid_repo.list_available_stages(
        step_ids=[row["step_id"] for row in records],
    )
    steps = [
        _build_step_record_response(
            dict(row),
            available.get(row["step_id"], []),
        )
        for row in records
    ]

    return ScenarioExecutionResponse(
        id=execution["id"],
        project_id=execution["project_id"],
        scenario_id=execution["scenario_id"],
        status=execution["status"],
        created_at=execution["created_at"],
        completed_at=execution.get("completed_at"),
        steps=steps,
    )


@router.post(
    "/{project_id}/scenario-executions/{exec_id}/steps/{record_id}/auto",
    response_model=ScenarioExecutionStatusResponse,
)
@inject
async def run_auto_step(
    project_id: UUID,
    exec_id: UUID,
    record_id: UUID,
    request: StepAutoExecuteRequest,
    session: FromDishka[MainAsyncSession],
) -> ScenarioExecutionStatusResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    execution_repo = SqlalchemyExecutionRepository(session)
    behave_config = await execution_repo.get_behave_config(project_id=project_id)
    if behave_config is None:
        raise HTTPException(status_code=404, detail="Behave config not found")

    behave_work_dir = Path(behave_config["behave_work_dir"])
    if not behave_work_dir.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Behave work dir not found: {behave_work_dir}",
        )

    hybrid_repo = SqlalchemyHybridRepository(session)
    execution = await hybrid_repo.get_scenario_execution(
        project_id=project_id, exec_id=exec_id
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Scenario execution not found")
    coverage_repo = SqlalchemyCoverageRepository(session)
    lookup_repo = ExecutionLookupRepository(session)
    service = HybridExecutionService(
        hybrid_repo=hybrid_repo,
        execution_repo=execution_repo,
        coverage_repo=coverage_repo,
        lookup_repo=lookup_repo,
        log_root=Path.cwd() / ".cache" / "bdd-hybrid",
        auto_policy=StepAutoPolicy(hybrid_repo),
    )
    await service.run_auto_step(
        project_id=project_id,
        exec_id=exec_id,
        record_id=record_id,
        stage_name=request.stage_name,
        behave_work_dir=behave_work_dir,
    )
    status_value = await service.finalize_execution(exec_id=exec_id)
    await session.commit()
    return ScenarioExecutionStatusResponse(status=status_value)


@router.patch(
    "/{project_id}/scenario-executions/{exec_id}/steps/{record_id}/manual",
    response_model=ScenarioExecutionStatusResponse,
)
@inject
async def update_manual_step(
    project_id: UUID,
    exec_id: UUID,
    record_id: UUID,
    request: StepManualUpdateRequest,
    session: FromDishka[MainAsyncSession],
) -> ScenarioExecutionStatusResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    hybrid_repo = SqlalchemyHybridRepository(session)
    execution = await hybrid_repo.get_scenario_execution(
        project_id=project_id, exec_id=exec_id
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Scenario execution not found")
    execution_repo = SqlalchemyExecutionRepository(session)
    coverage_repo = SqlalchemyCoverageRepository(session)
    lookup_repo = ExecutionLookupRepository(session)
    service = HybridExecutionService(
        hybrid_repo=hybrid_repo,
        execution_repo=execution_repo,
        coverage_repo=coverage_repo,
        lookup_repo=lookup_repo,
        log_root=Path.cwd() / ".cache" / "bdd-hybrid",
        auto_policy=StepAutoPolicy(hybrid_repo),
    )
    await service.update_manual_step(
        record_id=record_id,
        status=request.status,
        executor=request.executor,
        notes=request.notes,
    )
    status_value = await service.finalize_execution(exec_id=exec_id)
    await session.commit()
    return ScenarioExecutionStatusResponse(status=status_value)


@router.get("/{project_id}/features/{feature_id}", response_model=FeatureDetailResponse)
@inject
async def get_feature_detail(
    project_id: UUID,
    feature_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> FeatureDetailResponse:
    repo = _get_repo(session)
    await _ensure_project_exists(repo=repo, project_id=project_id)

    features_repo = SqlalchemyFeatureRepository(session)
    feature = await features_repo.get_feature_by_project(
        project_id=project_id,
        feature_id=feature_id,
    )
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    return FeatureDetailResponse(
        id=feature["id"],
        project_id=feature["project_id"],
        file_path=feature["file_path"],
        feature_name=feature["feature_name"],
        content=_to_utf8_text(feature.get("content")),
        git_sha=feature.get("git_sha"),
    )


@router.post(
    "/{project_id}/features",
    response_model=FeatureDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_feature(
    project_id: UUID,
    request: FeatureCreateRequest,
    session: FromDishka[MainAsyncSession],
) -> FeatureDetailResponse:
    projects_repo = SqlalchemyProjectRepository(session)
    await _ensure_project_exists(repo=projects_repo, project_id=project_id)

    features_repo = SqlalchemyFeatureRepository(session)
    normalized_path = request.file_path.strip()
    if not normalized_path:
        raise HTTPException(status_code=400, detail="Feature file path is invalid")

    existing = await features_repo.get_feature_by_path(
        project_id=project_id,
        file_path=normalized_path,
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Feature path already exists")

    git_config = await projects_repo.get_git_config(project_id)
    if git_config is None:
        raise HTTPException(status_code=404, detail="Git config not found")

    git_sync = GitSyncService()
    checkout_dir = _prepare_checkout_dir(
        project_id=project_id,
        git_repo_url=git_config.git_repo_url,
        git_branch=git_config.git_branch,
        git_access_token_encrypted=git_config.git_access_token_encrypted,
        git_sync=git_sync,
    )

    repo_file = checkout_dir / normalized_path
    if repo_file.exists():
        raise HTTPException(status_code=409, detail="Feature path already exists")

    repo_file.parent.mkdir(parents=True, exist_ok=True)
    repo_file.write_text(request.content, encoding="utf-8")

    commit_message = (request.commit_message or "").strip()
    if not commit_message:
        commit_message = _default_create_commit_message(normalized_path)

    try:
        git_sync.add(repo_path=checkout_dir, paths=[normalized_path])
        git_sync.commit(repo_path=checkout_dir, message=commit_message)

        parser = GherkinFeatureParser()
        service = FeatureSyncService(
            projects=projects_repo,
            features=features_repo,
            parser=parser,
            git_sync=git_sync,
            checkout_root=_checkout_root(),
        )
        files = service._collect_feature_files(checkout_dir)
        await features_repo.replace_project_features(
            project_id=project_id,
            files=files,
        )

        git_sync.push(repo_path=checkout_dir)
    except Exception as exc:
        try:
            git_sync.reset_hard(repo_path=checkout_dir, ref="HEAD~1")
        except Exception:
            pass
        await session.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Feature create failed: {exc}",
        ) from exc

    await session.commit()

    created = await features_repo.get_feature_by_path(
        project_id=project_id,
        file_path=normalized_path,
    )
    if created is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    return FeatureDetailResponse(
        id=created["id"],
        project_id=created["project_id"],
        file_path=created["file_path"],
        feature_name=created["feature_name"],
        content=_to_utf8_text(created.get("content")),
        git_sha=created.get("git_sha"),
    )


@router.post(
    "/{project_id}/features/{feature_id}/sub-features",
    response_model=FeatureDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_sub_feature(
    project_id: UUID,
    feature_id: UUID,
    request: SubFeatureCreateRequest,
    session: FromDishka[MainAsyncSession],
) -> FeatureDetailResponse:
    projects_repo = SqlalchemyProjectRepository(session)
    await _ensure_project_exists(repo=projects_repo, project_id=project_id)

    features_repo = SqlalchemyFeatureRepository(session)
    parent = await features_repo.get_feature_by_project(
        project_id=project_id,
        feature_id=feature_id,
    )
    if parent is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    git_config = await projects_repo.get_git_config(project_id)
    if git_config is None:
        raise HTTPException(status_code=404, detail="Git config not found")

    git_sync = GitSyncService()
    checkout_dir = _prepare_checkout_dir(
        project_id=project_id,
        git_repo_url=git_config.git_repo_url,
        git_branch=git_config.git_branch,
        git_access_token_encrypted=git_config.git_access_token_encrypted,
        git_sync=git_sync,
    )

    parent_path = parent.get("file_path")
    if not isinstance(parent_path, str) or not parent_path.strip():
        raise HTTPException(status_code=400, detail="Parent feature path is invalid")

    override_path = (request.file_path or "").strip()
    if override_path:
        file_path = override_path
    else:
        file_path = _derive_sub_feature_path(parent_path, request.child_name.strip())

    if not file_path:
        raise HTTPException(status_code=400, detail="Feature file path is invalid")

    existing = await features_repo.get_feature_by_path(
        project_id=project_id,
        file_path=file_path,
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Feature path already exists")

    repo_file = checkout_dir / file_path
    if repo_file.exists():
        raise HTTPException(status_code=409, detail="Feature path already exists")

    repo_file.parent.mkdir(parents=True, exist_ok=True)
    repo_file.write_text(request.content, encoding="utf-8")

    commit_message = (request.commit_message or "").strip()
    if not commit_message:
        commit_message = _default_create_commit_message(file_path)

    try:
        git_sync.add(repo_path=checkout_dir, paths=[file_path])
        git_sync.commit(repo_path=checkout_dir, message=commit_message)

        parser = GherkinFeatureParser()
        service = FeatureSyncService(
            projects=projects_repo,
            features=features_repo,
            parser=parser,
            git_sync=git_sync,
            checkout_root=_checkout_root(),
        )
        files = service._collect_feature_files(checkout_dir)
        await features_repo.replace_project_features(
            project_id=project_id,
            files=files,
        )

        git_sync.push(repo_path=checkout_dir)
    except Exception as exc:
        try:
            git_sync.reset_hard(repo_path=checkout_dir, ref="HEAD~1")
        except Exception:
            pass
        await session.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Feature create failed: {exc}",
        ) from exc

    await session.commit()

    created = await features_repo.get_feature_by_path(
        project_id=project_id,
        file_path=file_path,
    )
    if created is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    return FeatureDetailResponse(
        id=created["id"],
        project_id=created["project_id"],
        file_path=created["file_path"],
        feature_name=created["feature_name"],
        content=_to_utf8_text(created.get("content")),
        git_sha=created.get("git_sha"),
    )


@router.put("/{project_id}/features/{feature_id}", response_model=FeatureDetailResponse)
@inject
async def update_feature(
    project_id: UUID,
    feature_id: UUID,
    request: FeatureUpdateRequest,
    session: FromDishka[MainAsyncSession],
) -> FeatureDetailResponse:
    projects_repo = SqlalchemyProjectRepository(session)
    await _ensure_project_exists(repo=projects_repo, project_id=project_id)

    features_repo = SqlalchemyFeatureRepository(session)
    feature = await features_repo.get_feature_by_project(
        project_id=project_id,
        feature_id=feature_id,
    )
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    git_config = await projects_repo.get_git_config(project_id)
    if git_config is None:
        raise HTTPException(status_code=404, detail="Git config not found")

    git_sync = GitSyncService()
    checkout_dir = _prepare_checkout_dir(
        project_id=project_id,
        git_repo_url=git_config.git_repo_url,
        git_branch=git_config.git_branch,
        git_access_token_encrypted=git_config.git_access_token_encrypted,
        git_sync=git_sync,
    )

    file_path = feature["file_path"]
    if not isinstance(file_path, str) or len(file_path.strip()) == 0:
        raise HTTPException(status_code=400, detail="Feature file path is invalid")

    repo_file = checkout_dir / file_path
    repo_file.parent.mkdir(parents=True, exist_ok=True)
    repo_file.write_text(request.content, encoding="utf-8")

    commit_message = (request.commit_message or "").strip()
    if not commit_message:
        commit_message = _default_commit_message(file_path)

    try:
        git_sync.add(repo_path=checkout_dir, paths=[file_path])
        git_sync.commit(repo_path=checkout_dir, message=commit_message)

        parser = GherkinFeatureParser()
        service = FeatureSyncService(
            projects=projects_repo,
            features=features_repo,
            parser=parser,
            git_sync=git_sync,
            checkout_root=_checkout_root(),
        )
        files = service._collect_feature_files(checkout_dir)
        await features_repo.replace_project_features(
            project_id=project_id,
            files=files,
        )

        git_sync.push(repo_path=checkout_dir)
    except Exception as exc:
        try:
            git_sync.reset_hard(repo_path=checkout_dir, ref="HEAD~1")
        except Exception:
            pass
        await session.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Feature save failed: {exc}",
        ) from exc

    await session.commit()

    updated = await features_repo.get_feature_by_project(
        project_id=project_id,
        feature_id=feature_id,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Feature not found")

    return FeatureDetailResponse(
        id=updated["id"],
        project_id=updated["project_id"],
        file_path=updated["file_path"],
        feature_name=updated["feature_name"],
        content=_to_utf8_text(updated.get("content")),
        git_sha=updated.get("git_sha"),
    )


def create_projects_router() -> APIRouter:
    return router


@router.post("/{project_id}/sync", response_model=ProjectSyncResponse)
@inject
async def sync_project_features(
    project_id: UUID,
    session: FromDishka[MainAsyncSession],
) -> ProjectSyncResponse:
    projects_repo = SqlalchemyProjectRepository(session)
    features_repo = SqlalchemyFeatureRepository(session)
    service = FeatureSyncService(
        projects=projects_repo,
        features=features_repo,
        parser=GherkinFeatureParser(),
        git_sync=GitSyncService(),
        checkout_root=Path.cwd() / ".cache" / "bdd-project-sync",
    )

    try:
        summary = await service.sync_project_features(project_id=project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except GitConfigNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Git config not found") from exc
    except FeatureSyncError as exc:
        raise HTTPException(status_code=502, detail=f"Git sync failed: {exc}") from exc

    await session.commit()
    return ProjectSyncResponse.model_validate(summary, from_attributes=True)
