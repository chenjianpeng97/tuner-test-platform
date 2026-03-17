import ast
import re
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Iterable
from uuid import UUID

from app.bdd.features.domain.feature_repository import BehaveStageSpec, StepCoverageSpec

_DECORATOR_RE = re.compile(
    r"@(?P<kind>given|when|then|step)\s*\(\s*"
    r"(?P<literal>(?:[rRuUbBfF]{0,2})?(?:\"(?:\\\\.|[^\"\\\\])*\"|\'(?:\\\\.|[^\'\\\\])*\'))"
    r"\s*\)"
)

_REGEX_META_RE = re.compile(r"[\\.^$*+?()\[\]{}|]")


@dataclass(slots=True, frozen=True)
class StepRow:
    step_id: UUID
    text: str


class StepCoverageAnalyzer:
    def discover_stages(self, root: Path) -> list[BehaveStageSpec]:
        stages: list[BehaveStageSpec] = []
        seen: set[str] = set()
        for path in sorted(root.rglob("*_steps")):
            if not path.is_dir():
                continue
            stage_name = path.name[: -len("_steps")]
            if not stage_name:
                continue
            if stage_name in seen:
                continue
            seen.add(stage_name)
            try:
                steps_dir_path = path.relative_to(root).as_posix()
            except ValueError:
                steps_dir_path = path.as_posix()
            stages.append(
                BehaveStageSpec(
                    stage_name=stage_name,
                    steps_dir_path=steps_dir_path,
                )
            )
        return stages

    def extract_stage_patterns(self, steps_dir: Path) -> list[str]:
        patterns: list[str] = []
        for file_path in sorted(steps_dir.rglob("*.py")):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            patterns.extend(self._extract_patterns(content))
        return patterns

    def build_coverages(
        self,
        *,
        steps: Iterable[StepRow],
        stage_patterns: dict[str, list[str]],
        stage_ids: dict[str, UUID],
    ) -> list[StepCoverageSpec]:
        compiled: dict[str, list[Pattern[str]]] = {}
        for stage_name, patterns in stage_patterns.items():
            compiled[stage_name] = [self._compile_pattern(p) for p in patterns]

        coverages: list[StepCoverageSpec] = []
        for step in steps:
            for stage_name, regexes in compiled.items():
                stage_id = stage_ids.get(stage_name)
                if stage_id is None:
                    continue
                covered = any(regex.fullmatch(step.text) for regex in regexes)
                coverages.append(
                    StepCoverageSpec(
                        step_id=step.step_id,
                        stage_id=stage_id,
                        coverage_status="covered" if covered else "uncovered",
                    )
                )
        return coverages

    @staticmethod
    def _extract_patterns(content: str) -> list[str]:
        patterns: list[str] = []
        for match in _DECORATOR_RE.finditer(content):
            literal = match.group("literal")
            if not literal:
                continue
            try:
                pattern = ast.literal_eval(literal)
            except (SyntaxError, ValueError):
                continue
            if isinstance(pattern, str) and pattern:
                patterns.append(pattern)
        return patterns

    @staticmethod
    def _compile_pattern(pattern: str) -> Pattern[str]:
        if "{" in pattern and "}" in pattern:
            return re.compile(StepCoverageAnalyzer._parse_style_to_regex(pattern))
        if _REGEX_META_RE.search(pattern):
            return re.compile(f"^{pattern}$")
        return re.compile(f"^{re.escape(pattern)}$")

    @staticmethod
    def _parse_style_to_regex(pattern: str) -> str:
        pieces: list[str] = []
        last = 0
        for match in re.finditer(r"\{[^}]+\}", pattern):
            start, end = match.span()
            if start > last:
                pieces.append(re.escape(pattern[last:start]))
            pieces.append(r"(.+)")
            last = end
        if last < len(pattern):
            pieces.append(re.escape(pattern[last:]))
        return f"^{''.join(pieces)}$"
