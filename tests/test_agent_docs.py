from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agents_md_is_exact_copy_of_claude_md():
    assert (ROOT / "AGENTS.md").read_bytes() == (ROOT / "CLAUDE.md").read_bytes()


def test_legacy_template_directory_is_removed_after_migration():
    assert not (ROOT / "claude-md").exists()
