from dataclasses import FrozenInstanceError

import pytest

import envycontrol_boot as boot


class RecordingRunner:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.calls = []

    def run(self, argv, *, verbose=False):
        self.calls.append((tuple(argv), verbose))
        return boot.CommandResult(returncode=self.returncode)


def test_boot_stage_rejects_empty_command():
    with pytest.raises(ValueError, match="empty"):
        boot.BootStage(name="invalid", argv=())


def test_boot_rebuild_plan_is_immutable():
    plan = boot.BootRebuildPlan(
        backend="dracut",
        stages=(boot.BootStage("initramfs", ("dracut", "-f", "--regenerate-all")),),
        evidence=(),
        diagnostics=(),
        use_inhibit=False,
    )

    with pytest.raises(FrozenInstanceError):
        plan.backend = "mkinitcpio"


def test_plan_executes_direct_command_without_inhibit():
    runner = RecordingRunner()
    plan = boot.BootRebuildPlan(
        backend="mkinitcpio",
        stages=(boot.BootStage("initramfs", ("mkinitcpio", "-P")),),
        evidence=(),
        diagnostics=(),
        use_inhibit=False,
    )

    plan.execute(runner, verbose=True)

    assert runner.calls == [(('mkinitcpio', '-P'), True)]


def test_inhibit_wraps_only_an_existing_valid_stage():
    runner = RecordingRunner()
    plan = boot.BootRebuildPlan(
        backend="dracut",
        stages=(boot.BootStage("initramfs", ("dracut", "-f", "--regenerate-all")),),
        evidence=(),
        diagnostics=(),
        use_inhibit=True,
    )

    plan.execute(runner)

    assert runner.calls == [((
        "systemd-inhibit",
        "--who=envycontrol",
        "--why",
        "Rebuilding boot artifacts",
        "--",
        "dracut",
        "-f",
        "--regenerate-all",
    ), False)]


def test_nonzero_stage_result_raises_domain_error():
    runner = RecordingRunner(returncode=1)
    plan = boot.BootRebuildPlan(
        backend="dracut",
        stages=(boot.BootStage("initramfs", ("dracut", "-f", "--regenerate-all")),),
        evidence=(),
        diagnostics=(),
        use_inhibit=False,
    )

    with pytest.raises(boot.BootRebuildCommandError, match="dracut"):
        plan.execute(runner)
