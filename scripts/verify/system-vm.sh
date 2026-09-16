#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIFY_DIR="$ROOT/scripts/verify"
FIXTURE_BIN="$ROOT/tests/system/fixtures/bin"

# This MUST be the first executable project action. It accepts no override
# arguments and hard-codes the production sentinel + virtualization detector.
"$VERIFY_DIR/require-disposable-vm.sh"

if [[ "$EUID" -ne 0 ]]; then
  echo "REFUSED: VM system verification must run as root inside the disposable VM." >&2
  exit 65
fi

if [[ "$#" -ne 0 ]]; then
  echo "REFUSED: system-vm.sh accepts no host/path override arguments." >&2
  exit 64
fi

export PATH="$FIXTURE_BIN:$PATH"
export ENVYCONTROL_TEST_COMMAND_LOG="${ENVYCONTROL_TEST_COMMAND_LOG:-$ROOT/.verify/system-command.log}"
mkdir -p "$(dirname "$ENVYCONTROL_TEST_COMMAND_LOG")"
: >"$ENVYCONTROL_TEST_COMMAND_LOG"
PYTHON="${PYTHON:-python3}"

run_envy() {
  "$PYTHON" "$ROOT/envycontrol.py" "$@"
}

assert_mode() {
  local expected="$1"
  local actual
  actual="$(run_envy --query)"
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL: expected mode '$expected', got '$actual'" >&2
    exit 70
  fi
  echo "PASS: mode=$expected"
}

assert_exists() {
  local path="$1"
  [[ -e "$path" ]] || { echo "FAIL: expected $path to exist" >&2; exit 71; }
  echo "PASS: exists $path"
}

assert_absent() {
  local path="$1"
  [[ ! -e "$path" ]] || { echo "FAIL: expected $path to be absent" >&2; exit 72; }
  echo "PASS: absent $path"
}

echo "VM-only destructive verification starting. The VM/snapshot must be discarded afterwards."

run_envy --switch integrated
assert_mode integrated
assert_exists /etc/modprobe.d/blacklist-nvidia.conf
assert_exists /etc/udev/rules.d/50-remove-nvidia.rules

run_envy --switch hybrid --rtd3 2
assert_mode hybrid
assert_exists /etc/modprobe.d/nvidia.conf
assert_exists /etc/udev/rules.d/80-nvidia-pm.rules
assert_absent /etc/modprobe.d/blacklist-nvidia.conf

run_envy --switch nvidia --dm gdm
assert_mode nvidia
assert_exists /etc/X11/xorg.conf
assert_exists /etc/modprobe.d/nvidia.conf

run_envy --reset
assert_mode hybrid
assert_absent /etc/X11/xorg.conf
assert_absent /etc/modprobe.d/nvidia.conf
assert_absent /etc/modprobe.d/blacklist-nvidia.conf

grep -q '^systemctl ' "$ENVYCONTROL_TEST_COMMAND_LOG"
grep -Eq '^(systemd-inhibit|update-initramfs|dracut|dracut-rebuild|mkinitcpio|rpm-ostree|make-initrd) ' "$ENVYCONTROL_TEST_COMMAND_LOG"
echo "PASS: external system commands were intercepted by VM fixtures"
echo "PASS: destructive VM verification completed; discard/revert the disposable VM now"
