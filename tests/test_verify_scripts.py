import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "verify" / "smoke-cli.sh"
SYSTEM_VM = ROOT / "scripts" / "verify" / "system-vm.sh"
MUTATION = ROOT / "scripts" / "run-mutation.sh"


def test_safe_smoke_script_passes_without_privileged_operations():
    result = subprocess.run([str(SMOKE)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "safe CLI smoke verification completed" in result.stdout


def test_system_vm_script_refuses_without_explicit_vm_opt_in():
    env = os.environ.copy()
    env.pop("ENVYCONTROL_SYSTEM_TEST_VM", None)
    result = subprocess.run([str(SYSTEM_VM)], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert "ENVYCONTROL_SYSTEM_TEST_VM=1" in result.stderr


def test_system_vm_script_has_no_host_force_escape_hatch():
    text = SYSTEM_VM.read_text()
    forbidden = ("--force-host", "--i-know-what-im-doing", "ALLOW_BARE_METAL")
    assert all(token not in text for token in forbidden)


def test_system_vm_guard_runs_before_mutating_commands():
    lines = [
        line.strip()
        for line in SYSTEM_VM.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    guard_index = next(i for i, line in enumerate(lines) if "require-disposable-vm.sh" in line)
    first_envy_index = next(i for i, line in enumerate(lines) if '"$PYTHON" "$ROOT/envycontrol.py"' in line)
    assert guard_index < first_envy_index


def test_mutation_runner_resolves_mutmut_before_sudo_systemd_boundary():
    text = MUTATION.read_text()
    resolve = 'mutmut_bin="$(command -v mutmut)"'
    assert resolve in text
    assert text.index(resolve) < text.index("sudo systemd-run")
    assert '"$mutmut_bin" run' in text
