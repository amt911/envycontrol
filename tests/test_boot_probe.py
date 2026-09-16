import dataclasses
import importlib
import importlib.util

import pytest

import envycontrol_boot as boot


def test_boot_module_exposes_domain_boundaries():
    spec = importlib.util.find_spec("envycontrol_boot")
    assert spec is not None, "envycontrol_boot module must exist"

    module = importlib.import_module("envycontrol_boot")

    expected = {
        "EvidenceKind",
        "DetectionEvidence",
        "DetectionResult",
        "CommandResult",
        "SystemProbe",
        "LocalSystemProbe",
        "BootRebuildError",
        "NoBootBackendFoundError",
        "AmbiguousBootBackendError",
        "UnsupportedBootIntegrationError",
        "BootRebuildCommandError",
    }
    assert expected <= set(dir(module))


def test_detection_evidence_is_immutable():
    evidence = boot.DetectionEvidence(
        kind=boot.EvidenceKind.EXPLICIT_CONFIG,
        description="initrd_generator=dracut",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.description = "changed"


def test_detection_result_reports_strongest_evidence():
    result = boot.DetectionResult(
        backend="dracut",
        evidence=(
            boot.DetectionEvidence(boot.EvidenceKind.BINARY_PRESENT, "binary"),
            boot.DetectionEvidence(boot.EvidenceKind.ACTIVE_INTEGRATION, "hook"),
        ),
    )

    assert result.strongest is boot.EvidenceKind.ACTIVE_INTEGRATION


def test_local_probe_reads_text_and_detects_commands(monkeypatch, tmp_path):
    config = tmp_path / "dracut.conf"
    config.write_text("hostonly=yes\n", encoding="utf-8")
    monkeypatch.setattr(
        boot.shutil,
        "which",
        lambda name: "/usr/bin/dracut" if name == "dracut" else None,
    )

    probe = boot.LocalSystemProbe()

    assert probe.exists(config) is True
    assert probe.is_file(config) is True
    assert probe.read_text(config) == "hostonly=yes\n"
    assert probe.read_text(tmp_path / "missing") is None
    assert probe.command_exists("dracut") is True
    assert probe.command_exists("mkinitcpio") is False


def test_local_probe_detects_hook_masked_to_dev_null(tmp_path):
    masked_hook = tmp_path / "90-mkinitcpio-install.hook"
    masked_hook.symlink_to("/dev/null")

    probe = boot.LocalSystemProbe()

    assert probe.is_masked(masked_hook) is True
    assert probe.is_masked(tmp_path / "missing") is False
