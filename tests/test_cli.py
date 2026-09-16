import logging
import subprocess
import sys
from pathlib import Path

import pytest

import envycontrol


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "envycontrol.py"


def test_help_is_safe_and_successful():
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--switch" in result.stdout
    assert "--cache-query" in result.stdout


def test_version_is_safe_and_reports_current_version():
    result = subprocess.run([sys.executable, str(SCRIPT), "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == envycontrol.VERSION


def test_no_arguments_prints_help_and_exits_one():
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "usage:" in result.stdout.lower()


def test_invalid_switch_is_rejected_by_argparse():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--switch", "invalid"], capture_output=True, text=True
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_query_prints_inferred_mode_without_root(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--query"])
    monkeypatch.setattr(envycontrol, "get_current_mode", lambda: "hybrid")
    envycontrol.main()
    assert capsys.readouterr().out.strip() == "hybrid"


def test_assert_root_rejects_non_root(monkeypatch, caplog):
    monkeypatch.setattr(envycontrol.os, "geteuid", lambda: 1000)
    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
        envycontrol.assert_root()
    assert exc.value.code == 1
    assert "requires root privileges" in caplog.text


def test_cache_query_dispatches_without_root(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--cache-query"])
    monkeypatch.setattr(envycontrol.CachedConfig, "show_cache_file", lambda: called.append(True))
    envycontrol.main()
    assert called == [True]
