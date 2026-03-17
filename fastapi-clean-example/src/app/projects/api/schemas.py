from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class GitConfigUpsertRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    git_repo_url: str
    git_branch: str = "main"
    git_access_token: str = Field(min_length=1)
    features_root: str = Field(default="features/")


class GitConfigResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: UUID
    git_repo_url: str
    git_branch: str
    features_root: str


class ProjectSyncResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    added: int
    updated: int
    deleted: int
    total: int
    synced_at: datetime


class FeatureTreeScenarioNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["scenario"] = "scenario"
    id: UUID
    name: str
    rule_name: str | None
    line_number: int | None
    coverage_status: Literal["covered", "failed", "uncovered"] = "uncovered"


class FeatureTreeRuleNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["rule"] = "rule"
    name: str
    scenarios: list[FeatureTreeScenarioNode]


class FeatureTreeNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["feature"] = "feature"
    id: UUID
    file_path: str
    feature_name: str
    depth: int
    scenario_count: int
    rules: list[FeatureTreeRuleNode]
    scenarios: list[FeatureTreeScenarioNode]
    children: list["FeatureTreeNode"]


class FeatureDetailResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    file_path: str
    feature_name: str
    content: str
    git_sha: str | None


class FeatureUpdateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    commit_message: str | None = None


class FeatureCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    file_path: str = Field(min_length=1)
    content: str
    commit_message: str | None = None


class SubFeatureCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    child_name: str = Field(min_length=1)
    content: str
    file_path: str | None = None
    commit_message: str | None = None


class StepSuggestionItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    keyword: str
    text: str


class TestRunImportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    test_run_id: UUID
    status: str
    total: int
    passed: int
    failed: int
    skipped: int


class CoverageSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_scenarios: int
    covered_scenarios: int
    failed_scenarios: int
    coverage_percentage: float


class TestPlanCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TestPlanUpdateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class TestPlanResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class TestPlanItemResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    test_plan_id: UUID
    scenario_id: UUID
    status: Literal["not_run", "pass", "fail", "skip", "blocked"]
    notes: str | None
    updated_at: datetime


class TestPlanBulkAddRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario_ids: list[UUID]


class TestPlanBulkAddResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    added: int
    skipped: int


class TestPlanItemStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["not_run", "pass", "fail", "skip", "blocked"]
    notes: str | None = None


class TestPlanProgressResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    not_run: int
    pass_count: int
    fail_count: int
    skip_count: int
    blocked_count: int


class TestPlanSyncRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    test_run_id: UUID


class TestPlanSyncResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    updated: int
    skipped: int


class TestRunCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    scope_type: Literal["project", "feature", "tag"]
    scope_value: str | None = None
    executor_config: dict[str, str] | None = None


class TestRunResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    status: str
    scope_type: str
    scope_value: str | None
    triggered_at: datetime
    completed_at: datetime | None


class ScenarioExecutionCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario_id: UUID
    test_plan_item_id: UUID | None = None


class StepExecutionRecordResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    step_id: UUID
    step_order: int
    keyword: str
    text: str
    execution_mode: str
    status: str
    stage_id: UUID | None
    executor: str | None
    executed_at: datetime | None
    notes: str | None
    error_message: str | None
    available_stages: list[str]


class ScenarioExecutionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    scenario_id: UUID
    status: str
    created_at: datetime
    completed_at: datetime | None
    steps: list[StepExecutionRecordResponse]


class StepManualUpdateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["pass", "fail", "skip"]
    notes: str | None = None
    executor: str | None = None


class StepAutoExecuteRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage_name: str


class ScenarioExecutionStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
