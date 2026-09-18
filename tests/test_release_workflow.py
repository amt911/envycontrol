import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_triggers_only_on_semver_tags():
    text = _workflow_text()
    assert "'v[0-9]+.[0-9]+.[0-9]+'" in text
    assert re.search(r"^on:\n  push:\n    tags:\n", text, re.MULTILINE)
    assert "branches:" not in text, "a release must come from a tag, never from a branch push"


def test_release_workflow_can_write_releases():
    assert re.search(r"^permissions:\n  contents: write$", _workflow_text(), re.MULTILINE)


def test_release_workflow_version_rewrite_matches_the_real_version_line():
    text = _workflow_text()
    sed_expressions = re.findall(r"s/(\^VERSION[^/]*)/", text)
    assert sed_expressions, "the workflow must rewrite the VERSION line from the tag"

    version_line = next(
        line
        for line in (ROOT / "envycontrol.py").read_text(encoding="utf-8").splitlines()
        if line.startswith("VERSION")
    )
    for expression in sed_expressions:
        assert re.match(expression.replace(r"\.", "."), version_line), (
            f"sed pattern {expression!r} no longer matches {version_line!r}"
        )
