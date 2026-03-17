from pathlib import Path

from uuid import uuid4

from app.bdd.features.gateway.step_coverage_analyzer import StepCoverageAnalyzer, StepRow


def test_step_coverage_analyzer_matches_patterns(tmp_path: Path) -> None:
    steps_dir = tmp_path / "http_steps"
    steps_dir.mkdir()
    steps_file = steps_dir / "steps.py"
    steps_file.write_text(
        """
from behave import given, when, then

@given('user {name} exists')
def step_impl(context, name):
    pass

@when("user logs in")
def step_impl(context):
    pass
""",
        encoding="utf-8",
    )

    analyzer = StepCoverageAnalyzer()
    patterns = analyzer.extract_stage_patterns(steps_dir)
    assert "user {name} exists" in patterns
    assert "user logs in" in patterns

    step1 = uuid4()
    step2 = uuid4()
    step3 = uuid4()
    stage_id = uuid4()
    steps = [
        StepRow(step_id=step1, text="user alice exists"),
        StepRow(step_id=step2, text="user logs in"),
        StepRow(step_id=step3, text="user logs out"),
    ]
    stage_ids = {"http": stage_id}
    coverages = analyzer.build_coverages(
        steps=steps,
        stage_patterns={"http": patterns},
        stage_ids=stage_ids,
    )

    covered = {c.step_id: c.coverage_status for c in coverages}
    assert covered[step1] == "covered"
    assert covered[step2] == "covered"
    assert covered[step3] == "uncovered"
