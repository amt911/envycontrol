#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$(command -v python3)}"
RUN_MUTATION="${RUN_MUTATION:-0}"
RUN_SYSTEM_VM="${RUN_SYSTEM_VM:-0}"

case "$RUN_MUTATION" in
  0|1) ;;
  *) echo "RUN_MUTATION must be 0 or 1" >&2; exit 64 ;;
esac
case "$RUN_SYSTEM_VM" in
  0|1) ;;
  *) echo "RUN_SYSTEM_VM must be 0 or 1" >&2; exit 64 ;;
esac

if [[ ! -x "$PYTHON" ]]; then
  echo "Python interpreter is not executable: $PYTHON" >&2
  exit 127
fi

echo "==> host-safe pytest"
"$PYTHON" -m pytest -v

echo "==> branch coverage gate"
"$PYTHON" -m pytest --cov=envycontrol --cov-branch --cov-report=term-missing

echo "==> Ruff"
ruff check envycontrol.py tests scripts

echo "==> mypy"
mypy envycontrol.py

echo "==> agent instruction parity"
cmp -s CLAUDE.md AGENTS.md

echo "==> safe CLI smoke"
./scripts/verify/smoke-cli.sh

echo "==> packaging smoke"
"$PYTHON" -m pip install -e .
envycontrol --version
"$PYTHON" -c 'import envycontrol; assert envycontrol.VERSION == "3.5.2"'

if [[ "$RUN_MUTATION" == "1" ]]; then
  echo "==> mutation quality"
  ./scripts/run-mutation.sh --advisory
else
  echo "Mutation: NOT EXECUTED — set RUN_MUTATION=1 to run the current mutation policy"
fi

if [[ "$RUN_SYSTEM_VM" == "1" ]]; then
  echo "==> disposable-VM system verification"
  ./scripts/verify/system-vm.sh
else
  echo "Destructive VM verification: NOT EXECUTED — requires disposable VM"
fi

echo "PR verification completed"
