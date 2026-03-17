from decimal import Decimal
import pytest

from app.bdd.coverage.gateway.junit_parser import JunitParseError, parse_junit_results


def test_parse_junit_results_parses_cases() -> None:
    xml = (
        "<?xml version='1.0'?><testsuite>"
        "<testcase classname='auth.feature' name='Login ok' time='0.12'/>"
        "<testcase classname='auth.feature' name='Login fail' time='0.34'>"
        "<failure message='boom'>trace</failure></testcase>"
        "<testcase classname='auth.feature' name='Login skip' time='0.01'>"
        "<skipped /></testcase>"
        "</testsuite>"
    ).encode("utf-8")

    results = parse_junit_results(xml)

    assert len(results) == 3
    assert results[0].feature_name == "auth.feature"
    assert results[0].scenario_name == "Login ok"
    assert results[0].status == "pass"
    assert results[0].duration_seconds == Decimal("0.12")
    assert results[1].status == "fail"
    assert results[1].error_message == "boom"
    assert results[2].status == "skip"


def test_parse_junit_results_invalid_xml() -> None:
    with pytest.raises(JunitParseError):
        parse_junit_results(b"<invalid")
