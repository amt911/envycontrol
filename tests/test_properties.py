from unittest.mock import patch

from hypothesis import given, strategies as st

import envycontrol


@given(
    bus=st.integers(min_value=0, max_value=255),
    device=st.integers(min_value=0, max_value=31),
    function=st.integers(min_value=0, max_value=7),
)
def test_valid_hex_pci_components_round_trip_to_decimal(bus, device, function):
    address = f"{bus:02x}:{device:02x}.{function:x}"
    output = f"{address} 3D controller: NVIDIA Corporation Device\n".encode()
    with patch.object(envycontrol.subprocess, "check_output", return_value=output):
        assert envycontrol.get_nvidia_gpu_pci_bus() == f"PCI:{bus}:{device}:{function}"


@given(
    blacklist=st.booleans(),
    integrated=st.booleans(),
    legacy_integrated=st.booleans(),
    xorg=st.booleans(),
    modeset=st.booleans(),
)
def test_mode_inference_always_returns_supported_mode(
    blacklist, integrated, legacy_integrated, xorg, modeset
):
    state = {
        envycontrol.BLACKLIST_PATH: blacklist,
        envycontrol.UDEV_INTEGRATED_PATH: integrated,
        "/lib/udev/rules.d/50-remove-nvidia.rules": legacy_integrated,
        envycontrol.XORG_PATH: xorg,
        envycontrol.MODESET_PATH: modeset,
    }

    with patch.object(envycontrol.os.path, "exists", side_effect=lambda path: state.get(path, False)):
        mode = envycontrol.get_current_mode()

    assert mode in envycontrol.SUPPORTED_MODES
    if blacklist and (integrated or legacy_integrated):
        assert mode == "integrated"
    elif xorg and modeset:
        assert mode == "nvidia"
    else:
        assert mode == "hybrid"
