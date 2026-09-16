import json
from types import SimpleNamespace

import pytest

import envycontrol


def _configure_cache(monkeypatch, tmp_path, mode="hybrid"):
    root = tmp_path / "state"
    root.mkdir()
    (root / "keep").write_text("keep")
    cache_path = root / "cache" / "envycontrol" / "cache.json"
    monkeypatch.setattr(envycontrol, "CACHE_FILE_PATH", str(cache_path))
    monkeypatch.setattr(envycontrol, "get_current_mode", lambda: mode)
    return cache_path


def test_create_cache_writes_pci_bus_json(monkeypatch, tmp_path):
    cache_path = _configure_cache(monkeypatch, tmp_path)
    monkeypatch.setattr(envycontrol, "get_nvidia_gpu_pci_bus", lambda: "PCI:1:0:0")
    config = envycontrol.CachedConfig(SimpleNamespace())

    config.create_cache_file()

    assert json.loads(cache_path.read_text()) == {"nvidia_gpu_pci_bus": "PCI:1:0:0"}


def test_cache_creation_requires_hybrid_mode(monkeypatch, tmp_path):
    _configure_cache(monkeypatch, tmp_path, mode="nvidia")
    config = envycontrol.CachedConfig(SimpleNamespace())
    with pytest.raises(ValueError, match="requires that the system be in the hybrid"):
        config.create_cache_file()


def test_read_cache_restores_cached_bus(monkeypatch, tmp_path):
    cache_path = _configure_cache(monkeypatch, tmp_path, mode="nvidia")
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text('{"nvidia_gpu_pci_bus":"PCI:10:31:3"}')
    config = envycontrol.CachedConfig(SimpleNamespace())

    config.read_cache_file()

    assert config.get_nvidia_gpu_pci_bus() == "PCI:10:31:3"


def test_read_missing_cache_outside_hybrid_raises(monkeypatch, tmp_path):
    _configure_cache(monkeypatch, tmp_path, mode="nvidia")
    config = envycontrol.CachedConfig(SimpleNamespace())
    with pytest.raises(ValueError, match="No cache present"):
        config.read_cache_file()


def test_show_missing_cache_prints_error(monkeypatch, tmp_path, capsys):
    cache_path = _configure_cache(monkeypatch, tmp_path)
    envycontrol.CachedConfig.show_cache_file()
    assert str(cache_path) in capsys.readouterr().out


def test_delete_cache_removes_file_and_cache_directories(monkeypatch, tmp_path):
    cache_path = _configure_cache(monkeypatch, tmp_path)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text("{}")

    envycontrol.CachedConfig.delete_cache_file()

    assert not cache_path.exists()
    assert not cache_path.parent.exists()


def test_adapter_uses_existing_cache_for_detection(monkeypatch, tmp_path):
    cache_path = _configure_cache(monkeypatch, tmp_path, mode="nvidia")
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text('{"nvidia_gpu_pci_bus":"PCI:5:0:0"}')
    original = envycontrol.get_nvidia_gpu_pci_bus
    config = envycontrol.CachedConfig(SimpleNamespace())

    try:
        with config.adapter():
            assert envycontrol.get_nvidia_gpu_pci_bus() == "PCI:5:0:0"
        # Characterise current behavior: adapter leaves the global rebound after exit.
        assert envycontrol.get_nvidia_gpu_pci_bus() == "PCI:5:0:0"
    finally:
        envycontrol.get_nvidia_gpu_pci_bus = original


def test_hybrid_adapter_refreshes_cache(monkeypatch, tmp_path):
    cache_path = _configure_cache(monkeypatch, tmp_path, mode="hybrid")
    monkeypatch.setattr(envycontrol, "get_nvidia_gpu_pci_bus", lambda: "PCI:7:0:0")
    config = envycontrol.CachedConfig(SimpleNamespace())

    with config.adapter():
        pass

    assert json.loads(cache_path.read_text()) == {"nvidia_gpu_pci_bus": "PCI:7:0:0"}
