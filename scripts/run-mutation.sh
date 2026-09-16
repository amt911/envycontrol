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

mutmut_bin="$(command -v mutmut)"
python_bin="$(command -v python)"
if [[ -z "$mutmut_bin" ]]; then
  echo "mutmut is not installed or not available on PATH" >&2
  exit 127
fi
if [[ -z "$python_bin" ]]; then
  echo "python is not installed or not available on PATH" >&2
  exit 127
fi

run_mutmut_in_cgroup() {
  if [[ "${CI:-}" == "true" ]]; then
    sudo systemd-run --scope --quiet \
      -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 \
      --setenv=PATH="$PATH" \
      --setenv=PYTHON="$python_bin" -- \
      "$mutmut_bin" run
  else
    systemd-run --user --scope --quiet \
      -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 \
      --setenv=PATH="$PATH" \
      --setenv=PYTHON="$python_bin" -- \
      "$mutmut_bin" run
  fi
}

rm -rf mutants mutation-results.txt
run_mutmut_in_cgroup
"$mutmut_bin" export-cicd-stats

checker=("$python_bin" scripts/check_mutation_score.py mutants/mutmut-cicd-stats.json --threshold 60)
if [[ "$advisory" -eq 1 ]]; then
  checker+=(--advisory)
fi
"${checker[@]}" 2>&1 | tee mutation-results.txt
