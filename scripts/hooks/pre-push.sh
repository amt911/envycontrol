#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ruff check envycontrol.py tests scripts
mypy envycontrol.py
./scripts/verify/smoke-cli.sh

systemd-run --user --scope --quiet \
  -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
  python -m pytest --cov=envycontrol --cov-branch --cov-report=term-missing

# Advisory only until this branch records a real >=60% baseline. Once promoted,
# remove --advisory; never lower the threshold.
./scripts/run-mutation.sh --advisory
