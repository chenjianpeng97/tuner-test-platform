from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(slots=True, frozen=True)
class SyncFeatureFile:
    file_path: str
    content: str
    feature_name: str
    git_sha: str | None
    parent_file_path: str | None
    depth: int
    scenarios: list["SyncScenario"]


@dataclass(slots=True, frozen=True)
class SyncScenario:
    rule_name: str | None
    scenario_name: str
    line_number: int | None
    tags: list[str]
    steps: list["SyncStep"]


@dataclass(slots=True, frozen=True)
class SyncStep:
    keyword: str
    text: str


@dataclass(slots=True, frozen=True)
class BehaveStageSpec:
    stage_name: str
    steps_dir_path: str


@dataclass(slots=True, frozen=True)
class StepCoverageSpec:
    step_id: UUID
    stage_id: UUID
    coverage_status: str


@dataclass(slots=True, frozen=True)
class FeatureSyncSummary:
    added: int
    updated: int
    deleted: int
    total: int
    synced_at: datetime


class FeatureRepository(Protocol):
    async def replace_project_features(
        self,
        *,
        project_id: UUID,
        files: list[SyncFeatureFile],
    ) -> FeatureSyncSummary: ...

    async def replace_behave_stages(
        self,
        *,
        project_id: UUID,
        stages: list[BehaveStageSpec],
    ) -> dict[str, UUID]: ...

    async def list_steps_by_project(
        self,
        *,
        project_id: UUID,
    ) -> list[dict[str, object]]: ...

    async def replace_step_coverages(
        self,
        *,
        project_id: UUID,
        coverages: list[StepCoverageSpec],
    ) -> None: ...

    async def list_available_stages_by_step_ids(
        self,
        *,
        step_ids: list[UUID],
    ) -> dict[UUID, list[str]]: ...
