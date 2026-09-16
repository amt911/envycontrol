#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ruff check envycontrol.py envycontrol_boot.py tests scripts
mypy envycontrol.py envycontrol_boot.py
./scripts/verify/smoke-cli.sh

systemd-run --user --scope --quiet \
  -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
  python -m pytest \
    --cov=envycontrol --cov=envycontrol_boot --cov-branch --cov-report=term-missing

# Blocking: the measured two-module baseline is above the mandatory 60% floor.
# Never lower the threshold to make a change pass; kill meaningful survivors instead.
./scripts/run-mutation.sh
