#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${PYTHON:-python3}"

help_output="$($PYTHON "$ROOT/envycontrol.py" --help)"
grep -q -- "--switch" <<<"$help_output"
grep -q -- "--cache-query" <<<"$help_output"
echo "PASS: --help exposes expected CLI options"

version_output="$($PYTHON "$ROOT/envycontrol.py" --version)"
expected_version="$($PYTHON -c "import sys; sys.path.insert(0, '$ROOT'); import envycontrol; print(envycontrol.VERSION)")"
[[ "$version_output" == "$expected_version" ]]
echo "PASS: --version reports $version_output"

echo "PASS: safe CLI smoke verification completed without system mutation"
