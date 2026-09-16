from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_claude_md_is_a_shim_that_imports_agents_md():
    lines = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert "@AGENTS.md" in lines
    assert not any(line.startswith("## ") for line in lines), "rules belong in AGENTS.md, not CLAUDE.md"


def test_legacy_template_directory_is_removed_after_migration():
    assert not (ROOT / "claude-md").exists()
