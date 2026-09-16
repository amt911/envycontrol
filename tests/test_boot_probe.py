import importlib
import importlib.util


def test_boot_module_exposes_domain_boundaries():
    spec = importlib.util.find_spec("envycontrol_boot")
    assert spec is not None, "envycontrol_boot module must exist"

    boot = importlib.import_module("envycontrol_boot")

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
    assert expected <= set(dir(boot))
