import logging
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

import envycontrol
import envycontrol_boot as boot


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


def _install_fake_cached_config(monkeypatch, calls):
    class FakeCachedConfig:
        def __init__(self, args):
            calls.append(("cached-init", args))

        @contextmanager
        def adapter(self):
            calls.append(("adapter-enter",))
            yield
            calls.append(("adapter-exit",))

        def create_cache_file(self):
            calls.append(("cache-create",))

        @staticmethod
        def delete_cache_file():
            calls.append(("cache-delete",))

        @staticmethod
        def show_cache_file():
            calls.append(("cache-query",))

    monkeypatch.setattr(envycontrol, "CachedConfig", FakeCachedConfig)


def test_main_cache_create_checks_root_and_dispatches(monkeypatch):
    calls = []
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--cache-create"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))

    envycontrol.main()

    labels = [entry[0] for entry in calls]
    assert labels == ["root", "cached-init", "cache-create"]


def test_main_cache_delete_checks_root_and_dispatches(monkeypatch):
    calls = []
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--cache-delete"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))

    envycontrol.main()

    assert [entry[0] for entry in calls] == ["root", "cache-delete"]


def test_main_switch_preflights_before_cache_adapter(monkeypatch):
    calls = []
    plan = object()
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--switch", "integrated"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))
    monkeypatch.setattr(
        envycontrol,
        "resolve_boot_rebuild_plan",
        lambda: calls.append(("preflight",)) or plan,
    )
    monkeypatch.setattr(
        envycontrol,
        "graphics_mode_switcher",
        lambda *args, **kwargs: calls.append(("switch", args, kwargs)),
    )

    envycontrol.main()

    labels = [entry[0] for entry in calls]
    assert labels == [
        "root",
        "preflight",
        "cached-init",
        "adapter-enter",
        "switch",
        "adapter-exit",
    ]
    assert calls[4][2]["boot_plan"] is plan


def test_main_switch_reports_ambiguous_preflight_before_cache_adapter(
    monkeypatch, caplog, capsys
):
    calls = []
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--switch", "integrated"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))

    def fail_preflight():
        raise boot.AmbiguousBootBackendError(
            "Multiple boot rebuild backends have equally strong evidence: "
            "dracut: active dracut pacman hook; "
            "mkinitcpio: active mkinitcpio pacman hook"
        )

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", fail_preflight)
    monkeypatch.setattr(
        envycontrol,
        "graphics_mode_switcher",
        lambda *args, **kwargs: calls.append(("switch",)),
    )

    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
        envycontrol.main()

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "dracut" in caplog.text
    assert "mkinitcpio" in caplog.text
    assert "No system files were modified." in captured.err
    assert "Operation completed successfully" not in captured.out
    assert calls == [("root",)]


def test_main_reset_sddm_dispatches_inside_cache_adapter(monkeypatch):
    calls = []
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--reset-sddm"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: calls.append(
            ("create", path, content, executable)
        ),
    )

    envycontrol.main()

    labels = [entry[0] for entry in calls]
    assert labels == ["cached-init", "adapter-enter", "root", "create", "adapter-exit"]
    assert calls[3][1:] == (
        envycontrol.SDDM_XSETUP_PATH,
        envycontrol.SDDM_XSETUP_CONTENT,
        True,
    )


def test_main_reset_preflights_before_cache_adapter_and_reuses_plan(monkeypatch):
    calls = []
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--reset"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))
    monkeypatch.setattr(
        envycontrol,
        "rebuild_initramfs",
        lambda: calls.append(("legacy-rebuild",)),
    )

    class FakePlan:
        def execute(self, runner, verbose=False):
            calls.append(("boot",))

    monkeypatch.setattr(
        envycontrol,
        "resolve_boot_rebuild_plan",
        lambda: calls.append(("preflight",)) or FakePlan(),
    )

    envycontrol.main()

    labels = [entry[0] for entry in calls]
    assert labels == [
        "root",
        "preflight",
        "cached-init",
        "adapter-enter",
        "cleanup",
        "cache-delete",
        "boot",
        "adapter-exit",
    ]
    assert "legacy-rebuild" not in labels


def test_main_reset_preflight_failure_happens_before_cache_adapter(
    monkeypatch, caplog, capsys
):
    calls = []
    _install_fake_cached_config(monkeypatch, calls)
    monkeypatch.setattr(sys, "argv", ["envycontrol", "--reset"])
    monkeypatch.setattr(envycontrol, "assert_root", lambda: calls.append(("root",)))
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))

    def fail_preflight():
        raise boot.NoBootBackendFoundError("No supported initramfs generator detected")

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", fail_preflight)

    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
        envycontrol.main()

    assert exc.value.code == 1
    assert "No supported initramfs generator" in caplog.text
    assert "No system files were modified." in capsys.readouterr().err
    assert calls == [("root",)]
