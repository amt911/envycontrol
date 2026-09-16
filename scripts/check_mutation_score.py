#!/usr/bin/env python3
"""Validate mutmut CI stats without treating timeouts as killed mutants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _non_negative_int(stats: dict[str, object], key: str) -> int:
    raw = stats.get(key, 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise ValueError(f"{key} must be a non-negative integer")
    return raw


def load_stats(path: Path) -> tuple[int, int, int, int, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("mutation stats must be a JSON object")

    stats: dict[str, object] = raw
    killed = _non_negative_int(stats, "killed")
    timeout = _non_negative_int(stats, "timeout")
    skipped = _non_negative_int(stats, "skipped")
    total = _non_negative_int(stats, "total")

    if "survived" in stats:
        survived = _non_negative_int(stats, "survived")
    else:
        # mutmut CI exports may omit an explicit survivor count. Derive it
        # conservatively and keep timeouts separate so resource starvation cannot
        # improve the trusted mutation score.
        survived = total - skipped - timeout - killed
        if survived < 0:
            raise ValueError("mutation totals are inconsistent")

    return killed, survived, timeout, skipped, total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stats", type=Path, help="JSON produced by `mutmut export-cicd-stats`")
    parser.add_argument("--threshold", type=float, default=60.0)
    parser.add_argument(
        "--advisory",
        action="store_true",
        help="report a sub-threshold measured baseline without failing the process",
    )
    args = parser.parse_args()

    if args.threshold < 60:
        print("ERROR: blocking/advisory mutation thresholds must be at least 60%", file=sys.stderr)
        return 2
    if args.threshold > 100:
        print("ERROR: mutation threshold cannot exceed 100%", file=sys.stderr)
        return 2

    try:
        killed, survived, timeout, skipped, total = load_stats(args.stats)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: invalid mutation stats: {exc}", file=sys.stderr)
        return 2

    executed = killed + survived
    if executed == 0:
        print(
            "ERROR: no executed mutants remain after excluding skipped mutants and timeouts",
            file=sys.stderr,
        )
        return 2

    score = 100.0 * killed / executed
    summary = (
        f"mutation: killed={killed} survived={survived} timeout={timeout} "
        f"skipped={skipped} total={total} score={score:.2f}% threshold={args.threshold:.2f}%"
    )
    print(summary)

    if score < args.threshold:
        message = (
            f"mutation score {score:.2f}% is below threshold {args.threshold:.2f}%; "
            "a timeout is never counted as a killed mutant"
        )
        if args.advisory:
            print(f"ADVISORY: {message}", file=sys.stderr)
            return 0
        print(f"ERROR: {message}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
