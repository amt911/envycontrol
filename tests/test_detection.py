import builtins
import io

import pytest

import envycontrol


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("01:00.0", "PCI:1:0:0"),
        ("0a:1f.3", "PCI:10:31:3"),
        ("0000:65:00.0", "PCI:101:0:0"),
    ],
)
def test_nvidia_pci_bus_is_converted_to_xorg_decimal(monkeypatch, address, expected):
    output = f"{address} VGA compatible controller: NVIDIA Corporation Device\n".encode()
    monkeypatch.setattr(envycontrol.subprocess, "check_output", lambda args: output)

    assert envycontrol.get_nvidia_gpu_pci_bus() == expected


def test_missing_nvidia_gpu_exits_with_guidance(monkeypatch, capsys):
    monkeypatch.setattr(
        envycontrol.subprocess,
        "check_output",
        lambda args: b"00:02.0 VGA compatible controller: Intel Corporation\n",
    )

    with pytest.raises(SystemExit) as exc:
        envycontrol.get_nvidia_gpu_pci_bus()

    assert exc.value.code == 1
    assert "Try switching to hybrid mode first!" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("00:02.0 VGA compatible controller: Intel Corporation UHD", "intel"),
        ("05:00.0 Display controller: Advanced Micro Devices, Inc. [AMD/ATI]", "amd"),
        ("01:00.0 VGA compatible controller: NVIDIA Corporation", None),
    ],
)
def test_igpu_vendor_detection(monkeypatch, line, expected):
    monkeypatch.setattr(envycontrol.subprocess, "check_output", lambda args: (line + "\n").encode())
    assert envycontrol.get_igpu_vendor() == expected


def test_display_manager_is_parsed_from_execstart(monkeypatch):
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *args, **kwargs: io.StringIO("[Service]\nExecStart=/usr/bin/sddm\n"),
    )
    assert envycontrol.get_display_manager() == "sddm"


def test_missing_display_manager_returns_none(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(builtins, "open", missing)
    assert envycontrol.get_display_manager() is None


def test_amd_provider_name_is_read_from_xrandr(monkeypatch):
    monkeypatch.setattr(envycontrol.os.path, "exists", lambda path: path == "/usr/bin/xrandr")
    monkeypatch.setattr(
        envycontrol.subprocess,
        "check_output",
        lambda args: b"Provider 1: id: 0x54 name:AMD Radeon Graphics\n",
    )
    assert envycontrol.get_amd_igpu_name() == "AMD Radeon Graphics"


def test_missing_xrandr_returns_none(monkeypatch):
    monkeypatch.setattr(envycontrol.os.path, "exists", lambda path: False)
    assert envycontrol.get_amd_igpu_name() is None


@pytest.mark.parametrize(
    ("present", "expected"),
    [
        ({envycontrol.BLACKLIST_PATH, envycontrol.UDEV_INTEGRATED_PATH}, "integrated"),
        ({envycontrol.BLACKLIST_PATH, "/lib/udev/rules.d/50-remove-nvidia.rules"}, "integrated"),
        ({envycontrol.XORG_PATH, envycontrol.MODESET_PATH}, "nvidia"),
        (set(), "hybrid"),
    ],
)
def test_current_mode_is_inferred_from_marker_files(monkeypatch, present, expected):
    monkeypatch.setattr(envycontrol.os.path, "exists", lambda path: path in present)
    assert envycontrol.get_current_mode() == expected
