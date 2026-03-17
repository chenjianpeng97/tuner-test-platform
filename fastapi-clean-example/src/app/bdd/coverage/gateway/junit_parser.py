from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from xml.etree import ElementTree


@dataclass(slots=True, frozen=True)
class JunitTestCase:
    feature_name: str
    scenario_name: str
    status: str
    duration_seconds: Decimal | None
    error_message: str | None
    stack_trace: str | None


class JunitParseError(ValueError):
    pass


def _parse_duration(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def parse_junit_results(payload: bytes) -> list[JunitTestCase]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise JunitParseError(str(exc)) from exc

    results: list[JunitTestCase] = []
    for testcase in root.iter("testcase"):
        classname = testcase.get("classname") or ""
        name = testcase.get("name") or ""
        time = testcase.get("time")
        status = "pass"
        error_message = None
        stack_trace = None

        failure = testcase.find("failure")
        error = testcase.find("error")
        skipped = testcase.find("skipped")
        if failure is not None or error is not None:
            status = "fail"
            target = failure or error
            if target is not None:
                error_message = target.get("message")
                stack_trace = target.text
        elif skipped is not None:
            status = "skip"

        results.append(
            JunitTestCase(
                feature_name=classname,
                scenario_name=name,
                status=status,
                duration_seconds=_parse_duration(time),
                error_message=error_message,
                stack_trace=stack_trace,
            )
        )
    return results
