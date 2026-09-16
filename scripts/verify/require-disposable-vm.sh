#!/usr/bin/env bash
set -euo pipefail

require_disposable_vm() {
  local opt_in="${1-}"
  local sentinel="${2-}"
  local detector="${3-}"

  if [[ "$opt_in" != "1" ]]; then
    echo "REFUSED: set ENVYCONTROL_SYSTEM_TEST_VM=1 explicitly; destructive verification is VM-only." >&2
    return 20
  fi

  if [[ -z "$sentinel" || ! -f "$sentinel" ]]; then
    echo "REFUSED: disposable-VM sentinel is missing: ${sentinel:-<unset>}." >&2
    return 21
  fi

  local virt=""
  if ! virt="$("$detector" --vm 2>/dev/null)"; then
    echo "REFUSED: virtualization check failed; bare metal or an unknown environment is not a test target." >&2
    return 22
  fi

  virt="${virt//$'\r'/}"
  virt="${virt//$'\n'/}"
  if [[ -z "$virt" || "$virt" == "none" ]]; then
    echo "REFUSED: virtualization could not be positively identified." >&2
    return 23
  fi

  printf 'VM guard PASS: virtualization=%s; sentinel=%s\n' "$virt" "$sentinel"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  if [[ "$#" -ne 0 ]]; then
    echo "REFUSED: this guard accepts no command-line overrides." >&2
    exit 64
  fi

  require_disposable_vm \
    "${ENVYCONTROL_SYSTEM_TEST_VM:-}" \
    "/etc/envycontrol-test-vm" \
    "systemd-detect-virt"
fi
