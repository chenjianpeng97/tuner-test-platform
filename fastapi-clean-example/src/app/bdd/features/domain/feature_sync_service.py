from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.bdd.features.domain.feature_repository import (
    FeatureRepository,
    FeatureSyncSummary,
    SyncFeatureFile,
    SyncScenario,
    SyncStep,
)
from app.bdd.features.gateway.gherkin_parser import GherkinFeatureParser
from app.bdd.features.gateway.step_coverage_analyzer import (
    StepCoverageAnalyzer,
    StepRow,
)
from app.projects.gateway.git_sync_service import GitSyncService
from app.projects.gateway.sqlalchemy_project_repo import SqlalchemyProjectRepository


class FeatureSyncError(Exception):
    pass


class ProjectNotFoundError(FeatureSyncError):
    pass


class GitConfigNotFoundError(FeatureSyncError):
    pass


@dataclass(slots=True, frozen=True)
class FeatureSyncService:
    projects: SqlalchemyProjectRepository
    features: FeatureRepository
    parser: GherkinFeatureParser
    git_sync: GitSyncService
    checkout_root: Path

    async def sync_project_features(self, *, project_id: UUID) -> FeatureSyncSummary:
        project = await self.projects.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError

        git_config = await self.projects.get_git_config(project_id)
        if git_config is None:
            raise GitConfigNotFoundError

        checkout_dir = self.checkout_root / str(project_id)
        checkout_dir.parent.mkdir(parents=True, exist_ok=True)

        token = self._decode_token(git_config.git_access_token_encrypted)
        repo_url = self._inject_pat(git_config.git_repo_url, token)

        try:
            git_dir = checkout_dir / ".git"
            if git_dir.exists():
                self.git_sync.pull(repo_path=checkout_dir)
            else:
                self.git_sync.clone(
                    repo_url=repo_url,
                    branch=git_config.git_branch,
                    dst_path=checkout_dir,
                )
        except Exception as exc:
            raise FeatureSyncError(str(exc)) from exc

        features_root = self._resolve_features_root(git_config.features_root)
        scan_root = checkout_dir / features_root if features_root else checkout_dir
        files = self._collect_feature_files(scan_root)
        summary = await self.features.replace_project_features(
            project_id=project_id,
            files=files,
        )
        await self._refresh_stage_coverages(
            project_id=project_id,
            checkout_dir=checkout_dir,
        )
        return summary

    async def _refresh_stage_coverages(
        self,
        *,
        project_id: UUID,
        checkout_dir: Path,
    ) -> None:
        analyzer = StepCoverageAnalyzer()
        stages = analyzer.discover_stages(checkout_dir)
        stage_id_map = await self.features.replace_behave_stages(
            project_id=project_id,
            stages=stages,
        )

        steps_rows = await self.features.list_steps_by_project(project_id=project_id)
        steps = [
            StepRow(step_id=row["id"], text=row["text"])
            for row in steps_rows
            if isinstance(row.get("id"), UUID) and isinstance(row.get("text"), str)
        ]

        stage_patterns: dict[str, list[str]] = {}
        for stage in stages:
            steps_dir = checkout_dir / stage.steps_dir_path
            stage_patterns[stage.stage_name] = analyzer.extract_stage_patterns(steps_dir)

        coverages = analyzer.build_coverages(
            steps=steps,
            stage_patterns=stage_patterns,
            stage_ids=stage_id_map,
        )
        await self.features.replace_step_coverages(
            project_id=project_id,
            coverages=coverages,
        )

    @staticmethod
    def _decode_token(encrypted: bytes) -> str | None:
        if not encrypted:
            return None
        try:
            return encrypted.decode("utf-8")
        except UnicodeDecodeError:
            return None

    @staticmethod
    def _inject_pat(repo_url: str, token: str | None) -> str:
        if token is None:
            return repo_url
        if not repo_url.startswith("https://"):
            return repo_url
        prefix = "https://"
        url_body = repo_url[len(prefix) :]
        if "@" in url_body:
            return repo_url
        return f"{prefix}{token}@{url_body}"

    def _collect_feature_files(self, root: Path) -> list[SyncFeatureFile]:
        if not root.exists() or not root.is_dir():
            return []
        file_paths = [
            path for path in sorted(root.rglob("*.feature")) if path.is_file()
        ]
        relative_paths = {path.relative_to(root).as_posix() for path in file_paths}
        parent_map = {
            path.relative_to(root).as_posix(): FeatureSyncService._resolve_parent_path(
                path=path,
                root=root,
                relative_paths=relative_paths,
            )
            for path in file_paths
        }
        depth_map = FeatureSyncService._build_depth_map(parent_map)

        rows: list[SyncFeatureFile] = []
        for file_path in file_paths:
            if not file_path.is_file():
                continue
            content = file_path.read_text(encoding="utf-8")
            relative = file_path.relative_to(root).as_posix()
            rows.append(
                SyncFeatureFile(
                    file_path=relative,
                    content=content,
                    feature_name=FeatureSyncService._extract_feature_name(
                        content,
                        default=file_path.stem,
                    ),
                    git_sha=None,
                    parent_file_path=parent_map[relative],
                    depth=depth_map[relative],
                    scenarios=self._parse_scenarios(content),
                )
            )
        return rows

    @staticmethod
    def _resolve_features_root(value: str | None) -> str | None:
        if value is None:
            return "features/"
        cleaned = value.strip()
        if cleaned in {"", ".", "./"}:
            return None
        if cleaned.startswith("/"):
            cleaned = cleaned.lstrip("/")
        return cleaned

    def _parse_scenarios(self, content: str) -> list[SyncScenario]:
        parsed = self.parser.parse_scenarios(content)
        return [
            SyncScenario(
                rule_name=item.rule_name,
                scenario_name=item.scenario_name,
                line_number=item.line_number,
                tags=item.tags,
                steps=[
                    SyncStep(keyword=step.keyword, text=step.text)
                    for step in item.steps
                ],
            )
            for item in parsed
        ]

    @staticmethod
    def _resolve_parent_path(
        *,
        path: Path,
        root: Path,
        relative_paths: set[str],
    ) -> str | None:
        current = path.parent
        while current != root and current.is_relative_to(root):
            candidate = (current.parent / f"{current.name}.feature").relative_to(root)
            candidate_path = candidate.as_posix()
            if candidate_path in relative_paths:
                return candidate_path
            current = current.parent
        return None

    @staticmethod
    def _build_depth_map(parent_map: dict[str, str | None]) -> dict[str, int]:
        depth_map: dict[str, int] = {}

        def resolve_depth(path: str) -> int:
            cached = depth_map.get(path)
            if cached is not None:
                return cached
            parent = parent_map.get(path)
            if parent is None:
                depth_map[path] = 0
                return 0
            depth = resolve_depth(parent) + 1
            depth_map[path] = depth
            return depth

        for path in parent_map:
            resolve_depth(path)
        return depth_map

    @staticmethod
    def _extract_feature_name(content: str, *, default: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("feature:"):
                return stripped.split(":", 1)[1].strip() or default
        return default
