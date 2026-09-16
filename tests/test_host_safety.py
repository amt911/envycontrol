from types import SimpleNamespace

import pytest

import envycontrol
from conftest import UnsafeHostMutation


def test_real_etc_write_is_blocked():
    with pytest.raises(UnsafeHostMutation, match="protected write"):
        envycontrol.create_file("/etc/modprobe.d/envycontrol-test.conf", "unsafe")


def test_real_systemctl_is_blocked():
    with pytest.raises(UnsafeHostMutation, match="dangerous command: systemctl"):
        envycontrol.subprocess.run(["systemctl", "disable", "nvidia-persistenced.service"])


def test_real_lspci_is_blocked():
    with pytest.raises(UnsafeHostMutation, match="host discovery command: lspci"):
        envycontrol.subprocess.check_output(["lspci"])


def test_tmp_path_write_is_allowed(tmp_path):
    target = tmp_path / "generated.conf"
    envycontrol.create_file(str(target), "safe")
    assert target.read_text() == "safe"


def test_mode_switch_can_replace_dangerous_boundaries_with_fakes(monkeypatch):
    calls = []
    files = []

    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: calls.append(tuple(args)) or SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: files.append((path, content, executable)),
    )
    monkeypatch.setattr(envycontrol, "rebuild_initramfs", lambda: calls.append(("initramfs",)))

    envycontrol.graphics_mode_switcher("integrated", None, False, None, None, False)

    assert ("systemctl", "disable", "nvidia-persistenced.service") in calls
    assert ("cleanup",) in calls
    assert ("initramfs",) in calls
    assert [entry[0] for entry in files] == [
        envycontrol.BLACKLIST_PATH,
        envycontrol.UDEV_INTEGRATED_PATH,
    ]
