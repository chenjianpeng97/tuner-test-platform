from dataclasses import dataclass
from typing import Any

from gherkin.parser import Parser


@dataclass(slots=True, frozen=True)
class ParsedStep:
    keyword: str
    text: str


@dataclass(slots=True, frozen=True)
class ParsedScenario:
    rule_name: str | None
    scenario_name: str
    line_number: int | None
    tags: list[str]
    steps: list[ParsedStep]


class GherkinFeatureParser:
    def parse_scenarios(self, content: str) -> list[ParsedScenario]:
        document = Parser().parse(content)
        return self._extract_scenarios(document)

    def _extract_scenarios(self, document: dict[str, Any]) -> list[ParsedScenario]:
        rows: list[ParsedScenario] = []
        for scenario_data, rule_name in self._iter_scenarios(document):
            parsed = self._parse_scenario(scenario_data, rule_name=rule_name)
            if parsed is not None:
                rows.append(parsed)
        return rows

    def _iter_scenarios(
        self,
        document: dict[str, Any],
    ) -> list[tuple[dict[str, Any], str | None]]:
        feature = document.get("feature")
        if not isinstance(feature, dict):
            return []

        children = feature.get("children")
        if not isinstance(children, list):
            return []

        rows: list[tuple[dict[str, Any], str | None]] = []
        for child in children:
            if not isinstance(child, dict):
                continue
            rows.extend(self._iter_from_child(child))
        return rows

    def _iter_from_child(
        self,
        child: dict[str, Any],
    ) -> list[tuple[dict[str, Any], str | None]]:
        scenario = child.get("scenario")
        if isinstance(scenario, dict):
            return [(scenario, None)]

        rule = child.get("rule")
        if not isinstance(rule, dict):
            return []

        rule_name = self._as_non_empty_str(rule.get("name"))
        rule_children = rule.get("children")
        if not isinstance(rule_children, list):
            return []

        rows: list[tuple[dict[str, Any], str | None]] = []
        for rule_child in rule_children:
            if not isinstance(rule_child, dict):
                continue
            rule_scenario = rule_child.get("scenario")
            if isinstance(rule_scenario, dict):
                rows.append((rule_scenario, rule_name))
        return rows

    def _parse_scenario(
        self,
        scenario: dict[str, Any],
        *,
        rule_name: str | None,
    ) -> ParsedScenario | None:
        scenario_name = self._as_non_empty_str(scenario.get("name"))
        if scenario_name is None:
            return None

        line_number = self._extract_line_number(scenario.get("location"))
        tags = self._extract_tags(scenario.get("tags"))
        steps = self._extract_steps(scenario.get("steps"))

        return ParsedScenario(
            rule_name=rule_name,
            scenario_name=scenario_name,
            line_number=line_number,
            tags=tags,
            steps=steps,
        )

    @staticmethod
    def _extract_steps(raw_steps: Any) -> list[ParsedStep]:
        if not isinstance(raw_steps, list):
            return []
        rows: list[ParsedStep] = []
        for item in raw_steps:
            if not isinstance(item, dict):
                continue
            keyword = item.get("keyword")
            text = item.get("text")
            if not isinstance(keyword, str) or not isinstance(text, str):
                continue
            rows.append(ParsedStep(keyword=keyword.strip(), text=text.strip()))
        return rows

    @staticmethod
    def _extract_tags(raw_tags: Any) -> list[str]:
        if not isinstance(raw_tags, list):
            return []
        rows: list[str] = []
        for item in raw_tags:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if isinstance(name, str) and len(name) > 0:
                rows.append(name)
        return rows

    @staticmethod
    def _extract_line_number(location: Any) -> int | None:
        if not isinstance(location, dict):
            return None
        line = location.get("line")
        if isinstance(line, int):
            return line
        return None

    @staticmethod
    def _as_non_empty_str(value: Any) -> str | None:
        if isinstance(value, str) and len(value.strip()) > 0:
            return value.strip()
        return None
