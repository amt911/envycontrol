import logging

import pytest

import envycontrol
import envycontrol_boot as boot


def test_rebuild_initramfs_executes_one_resolved_plan(monkeypatch):
    events = []

    class FakePlan:
        def execute(self, runner, verbose=False):
            events.append(("execute", type(runner).__name__, verbose))

    monkeypatch.setattr(
        envycontrol,
        "resolve_boot_rebuild_plan",
        lambda: events.append(("resolve",)) or FakePlan(),
    )

    envycontrol.rebuild_initramfs()

    assert events == [
        ("resolve",),
        ("execute", "SubprocessCommandRunner", False),
    ]


def test_rebuild_initramfs_uses_verbose_runner_when_debugging(monkeypatch):
    verbose_values = []

    class FakePlan:
        def execute(self, runner, verbose=False):
            verbose_values.append(verbose)

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", lambda: FakePlan())
    monkeypatch.setattr(logging.getLogger(), "level", logging.DEBUG)

    envycontrol.rebuild_initramfs()

    assert verbose_values == [True]


def test_rebuild_initramfs_propagates_preflight_failure_before_command_execution(
    monkeypatch,
):
    commands = []

    def fail_preflight():
        raise boot.NoBootBackendFoundError("no supported backend")

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", fail_preflight)
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda *args, **kwargs: commands.append(args),
    )

    with pytest.raises(boot.NoBootBackendFoundError, match="no supported backend"):
        envycontrol.rebuild_initramfs()

    assert commands == []


def test_rebuild_initramfs_propagates_stage_failure(monkeypatch):
    class FailingPlan:
        def execute(self, runner, verbose=False):
            raise boot.BootRebuildCommandError("dracut failed")

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", lambda: FailingPlan())

    with pytest.raises(boot.BootRebuildCommandError, match="dracut failed"):
        envycontrol.rebuild_initramfs()
