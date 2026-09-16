import envycontrol


def test_intel_xorg_template_embeds_pci_bus():
    config = envycontrol.XORG_INTEL.format("PCI:1:0:0")
    assert 'Driver "nvidia"' in config
    assert 'BusID "PCI:1:0:0"' in config
    assert 'Inactive "intel"' in config


def test_amd_xorg_template_embeds_pci_bus():
    config = envycontrol.XORG_AMD.format("PCI:101:0:0")
    assert 'BusID "PCI:101:0:0"' in config
    assert 'Inactive "amdgpu"' in config


def test_intel_xrandr_script_uses_modesetting_provider():
    script = envycontrol.generate_xrandr_script("intel")
    assert 'xrandr --setprovideroutputsource "modesetting" NVIDIA-0' in script


def test_amd_xrandr_script_uses_detected_provider(monkeypatch):
    monkeypatch.setattr(envycontrol, "get_amd_igpu_name", lambda: "AMD Radeon Graphics")
    script = envycontrol.generate_xrandr_script("amd")
    assert 'xrandr --setprovideroutputsource "AMD Radeon Graphics" NVIDIA-0' in script


def test_amd_xrandr_script_falls_back_to_modesetting(monkeypatch):
    monkeypatch.setattr(envycontrol, "get_amd_igpu_name", lambda: None)
    assert '"modesetting" NVIDIA-0' in envycontrol.generate_xrandr_script("amd")


def test_unknown_igpu_falls_back_to_modesetting():
    assert '"modesetting" NVIDIA-0' in envycontrol.generate_xrandr_script(None)


def test_modeset_rtd3_templates_preserve_requested_value():
    assert "NVreg_DynamicPowerManagement=0x02" in envycontrol.MODESET_RTD3.format(2)
    assert "NVreg_DynamicPowerManagement=0x03" in envycontrol.MODESET_CURRENT_RTD3.format(3)
