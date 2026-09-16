import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "verify" / "require-disposable-vm.sh"


def _write_detector(tmp_path, body):
    detector = tmp_path / "detect-virt"
    detector.write_text("#!/usr/bin/env bash\n" + body + "\n")
    detector.chmod(0o755)
    return detector


def _run_guard_function(opt_in, sentinel, detector):
    command = (
        f"source {shlex.quote(str(GUARD))}; "
        f"require_disposable_vm {shlex.quote(opt_in)} "
        f"{shlex.quote(str(sentinel))} {shlex.quote(str(detector))}"
    )
    return subprocess.run(["bash", "-c", command], capture_output=True, text=True)


def test_guard_script_exists_before_any_system_verifier_is_added():
    assert GUARD.is_file()


def test_vm_guard_refuses_missing_opt_in(tmp_path):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("envycontrol test vm")
    detector = _write_detector(tmp_path, "echo kvm; exit 0")
    result = _run_guard_function("", sentinel, detector)
    assert result.returncode != 0
    assert "ENVYCONTROL_SYSTEM_TEST_VM=1" in result.stderr


def test_vm_guard_refuses_missing_sentinel(tmp_path):
    detector = _write_detector(tmp_path, "echo kvm; exit 0")
    result = _run_guard_function("1", tmp_path / "missing", detector)
    assert result.returncode != 0
    assert "sentinel" in result.stderr.lower()


def test_vm_guard_refuses_bare_metal_result(tmp_path):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("envycontrol test vm")
    detector = _write_detector(tmp_path, "echo none; exit 1")
    result = _run_guard_function("1", sentinel, detector)
    assert result.returncode != 0
    assert "virtual" in result.stderr.lower()


def test_vm_guard_refuses_ambiguous_virtualization_result(tmp_path):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("envycontrol test vm")
    detector = _write_detector(tmp_path, "printf ''; exit 0")
    result = _run_guard_function("1", sentinel, detector)
    assert result.returncode != 0
    assert "virtual" in result.stderr.lower()


def test_vm_guard_accepts_all_three_independent_gates(tmp_path):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("envycontrol test vm")
    detector = _write_detector(tmp_path, "echo kvm; exit 0")
    result = _run_guard_function("1", sentinel, detector)
    assert result.returncode == 0
    assert "kvm" in result.stdout
    assert "sentinel" in result.stdout.lower()
