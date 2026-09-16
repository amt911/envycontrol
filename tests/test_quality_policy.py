from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dependabot_uses_monthly_python_and_actions_updates():
    text = (ROOT / ".github" / "dependabot.yml").read_text()
    assert text.count("interval: monthly") == 2
    assert "interval: weekly" not in text


def test_security_workflow_is_blocking_and_checks_installed_environment():
    text = (ROOT / ".github" / "workflows" / "security.yml").read_text()
    assert "continue-on-error: true" not in text
    assert "python -m pip install -r requirements-dev.txt" in text
    assert "python -m pip check" in text
    assert "python -m pip_audit -r requirements-dev.txt" in text
    assert "semgrep scan --config p/python --config p/secrets" in text


def test_precommit_covers_whitespace_yaml_markdown_and_project_gates():
    text = (ROOT / ".pre-commit-config.yaml").read_text()
    required = (
        "https://github.com/pre-commit/pre-commit-hooks",
        "id: trailing-whitespace",
        "id: end-of-file-fixer",
        "id: check-yaml",
        "https://github.com/igorshubovych/markdownlint-cli",
        "id: markdownlint",
        "id: ruff",
        "id: agent-docs-identical",
        "id: safety-tests",
        "id: pre-push-quality",
    )
    for marker in required:
        assert marker in text


def test_mutation_workflow_is_path_scoped_and_uploads_readable_result():
    text = (ROOT / ".github" / "workflows" / "mutation.yml").read_text()
    assert "paths:" in text
    assert "envycontrol.py" in text
    assert "tests/**" in text
    assert "scripts/**" in text
    assert "mutation-results.txt" in text
