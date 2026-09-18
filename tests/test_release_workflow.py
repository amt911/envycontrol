import os
import re
import shutil
import subprocess
import sys
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


def _stamp_script() -> str:
    """The shell of the workflow step that rewrites the version, verbatim."""
    text = _workflow_text()
    block = text[text.index("- name: Stamp the version from the tag") :]
    block = block[block.index("run: |") + len("run: |") :]
    lines = []
    for line in block.splitlines()[1:]:
        if line.strip() and not line.startswith(" " * 10):
            break
        lines.append(line[10:])
    return "\n".join(lines)


def test_stamping_a_tag_updates_every_declared_version(tmp_path):
    """Running the workflow's own shell must leave both files, and the CLI, on the tag."""
    for name in ("envycontrol.py", "envycontrol_boot.py", "flake.nix"):
        shutil.copy(ROOT / name, tmp_path / name)
    outputs = tmp_path / "gh_output"
    outputs.touch()

    subprocess.run(
        ["bash", "-c", _stamp_script()],
        cwd=tmp_path,
        env={
            "PATH": os.environ["PATH"],
            "GITHUB_REF_NAME": "v9.9.9",
            "GITHUB_OUTPUT": str(outputs),
        },
        check=True,
    )

    reported = subprocess.run(
        [sys.executable, "envycontrol.py", "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert reported.stdout.strip() == "9.9.9"
    assert 'version = "9.9.9";' in (tmp_path / "flake.nix").read_text(encoding="utf-8")
    assert "version=9.9.9" in outputs.read_text(encoding="utf-8")


def test_nix_package_version_matches_the_cli_version():
    """flake.nix repeats the version, so a bump that misses it ships a mislabelled package."""
    import envycontrol

    flake = (ROOT / "flake.nix").read_text(encoding="utf-8")
    declared = re.search(r'^\s*version = "([^"]+)";', flake, re.MULTILINE)
    assert declared, "flake.nix no longer declares a package version"
    assert declared.group(1) == envycontrol.VERSION
