from types import SimpleNamespace

import envycontrol


def _fake_run_recorder(monkeypatch, calls, returncode=0):
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: calls.append(tuple(args)) or SimpleNamespace(returncode=returncode),
    )


def _fake_boot_plan(monkeypatch, calls):
    class FakePlan:
        def execute(self, runner, verbose=False):
            calls.append(("initramfs",))

    monkeypatch.setattr(envycontrol, "resolve_boot_rebuild_plan", lambda: FakePlan())


def test_integrated_mode_records_expected_side_effects(monkeypatch):
    calls = []
    files = []
    _fake_run_recorder(monkeypatch, calls)
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: files.append((path, content, executable)),
    )
    _fake_boot_plan(monkeypatch, calls)

    envycontrol.graphics_mode_switcher("integrated", None, False, None, None, False)

    assert calls == [
        ("systemctl", "disable", "nvidia-persistenced.service"),
        ("cleanup",),
        ("initramfs",),
    ]
    assert files == [
        (envycontrol.BLACKLIST_PATH, envycontrol.BLACKLIST_CONTENT, False),
        (envycontrol.UDEV_INTEGRATED_PATH, envycontrol.UDEV_INTEGRATED, False),
    ]


def test_hybrid_mode_with_rtd3_writes_power_management_rules(monkeypatch):
    calls = []
    files = []
    _fake_run_recorder(monkeypatch, calls)
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: files.append((path, content, executable)),
    )
    _fake_boot_plan(monkeypatch, calls)

    envycontrol.graphics_mode_switcher("hybrid", None, False, None, 2, False)

    assert (envycontrol.MODESET_PATH, envycontrol.MODESET_RTD3.format(2), False) in files
    assert (envycontrol.UDEV_PM_PATH, envycontrol.UDEV_PM_CONTENT, False) in files
    assert ("systemctl", "enable", "nvidia-persistenced.service") in calls
    assert calls[-1] == ("initramfs",)


def test_hybrid_mode_can_generate_nvidia_current_config(monkeypatch):
    files = []
    _fake_run_recorder(monkeypatch, [])
    monkeypatch.setattr(envycontrol, "cleanup", lambda: None)
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: files.append((path, content, executable)),
    )
    _fake_boot_plan(monkeypatch, [])

    envycontrol.graphics_mode_switcher("hybrid", None, False, None, None, True)

    assert (envycontrol.MODESET_PATH, envycontrol.MODESET_CURRENT_CONTENT, False) in files


def test_nvidia_mode_writes_intel_lightdm_and_optional_settings(monkeypatch):
    calls = []
    files = []
    _fake_run_recorder(monkeypatch, calls)
    monkeypatch.setattr(envycontrol, "cleanup", lambda: calls.append(("cleanup",)))
    monkeypatch.setattr(envycontrol, "get_nvidia_gpu_pci_bus", lambda: "PCI:1:0:0")
    monkeypatch.setattr(envycontrol, "get_igpu_vendor", lambda: "intel")
    monkeypatch.setattr(
        envycontrol,
        "create_file",
        lambda path, content, executable=False: files.append((path, content, executable)),
    )
    _fake_boot_plan(monkeypatch, calls)

    envycontrol.graphics_mode_switcher("nvidia", "lightdm", True, 7, None, False)

    by_path = {path: (content, executable) for path, content, executable in files}
    assert 'BusID "PCI:1:0:0"' in by_path[envycontrol.XORG_PATH][0]
    assert by_path[envycontrol.MODESET_PATH][0] == envycontrol.MODESET_CONTENT
    assert envycontrol.FORCE_COMP in by_path[envycontrol.EXTRA_XORG_PATH][0]
    assert envycontrol.COOLBITS.format(7) in by_path[envycontrol.EXTRA_XORG_PATH][0]
    assert by_path[envycontrol.LIGHTDM_SCRIPT_PATH][1] is True
    assert by_path[envycontrol.LIGHTDM_CONFIG_PATH][0] == envycontrol.LIGHTDM_CONFIG_CONTENT
    assert calls[-1] == ("initramfs",)


def test_cleanup_removes_only_redirected_files_and_restores_sddm_backup(monkeypatch, tmp_path):
    managed = tmp_path / "managed"
    paths = {
        "BLACKLIST_PATH": managed / "blacklist.conf",
        "UDEV_INTEGRATED_PATH": managed / "integrated.rules",
        "UDEV_PM_PATH": managed / "pm.rules",
        "XORG_PATH": managed / "xorg.conf",
        "EXTRA_XORG_PATH": managed / "extra.conf",
        "MODESET_PATH": managed / "nvidia.conf",
        "LIGHTDM_SCRIPT_PATH": managed / "nvidia.sh",
        "LIGHTDM_CONFIG_PATH": managed / "lightdm.conf",
        "SDDM_XSETUP_PATH": managed / "Xsetup",
    }
    managed.mkdir()
    for name, path in paths.items():
        monkeypatch.setattr(envycontrol, name, str(path))
    for name, path in paths.items():
        if name != "SDDM_XSETUP_PATH":
            path.write_text(name)
    backup = paths["SDDM_XSETUP_PATH"].with_name("Xsetup.bak")
    backup.write_text("original xsetup")

    real_exists = envycontrol.os.path.exists
    prefix = str(tmp_path)
    monkeypatch.setattr(
        envycontrol.os.path,
        "exists",
        lambda path: real_exists(path) if str(path).startswith(prefix) else False,
    )

    envycontrol.cleanup()

    for name, path in paths.items():
        if name not in {"SDDM_XSETUP_PATH"}:
            assert not path.exists()
    assert paths["SDDM_XSETUP_PATH"].read_text() == "original xsetup"
    assert not backup.exists()
