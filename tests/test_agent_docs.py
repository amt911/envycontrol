from pathlib import Path


def test_agents_md_is_exact_copy_of_claude_md():
    root = Path(__file__).resolve().parents[1]
    assert (root / "AGENTS.md").read_bytes() == (root / "CLAUDE.md").read_bytes()
