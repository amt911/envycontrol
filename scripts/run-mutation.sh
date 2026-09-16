#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

advisory=0
if [[ "${1-}" == "--advisory" ]]; then
  advisory=1
  shift
fi
if [[ "$#" -ne 0 ]]; then
  echo "usage: $0 [--advisory]" >&2
  exit 64
fi

run_mutmut_in_cgroup() {
  if [[ "${CI:-}" == "true" ]]; then
    sudo systemd-run --scope --quiet \
      -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
      mutmut run
  else
    systemd-run --user --scope --quiet \
      -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
      mutmut run
  fi
}

rm -rf mutants
run_mutmut_in_cgroup
mutmut export-cicd-stats

checker=(python scripts/check_mutation_score.py mutants/mutmut-cicd-stats.json --threshold 60)
if [[ "$advisory" -eq 1 ]]; then
  checker+=(--advisory)
fi
"${checker[@]}"
