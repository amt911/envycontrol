import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_mutation_score.py"


def _run_checker(tmp_path, stats, threshold="60"):
    stats_path = tmp_path / "stats.json"
    stats_path.write_text(json.dumps(stats))
    return subprocess.run(
        [sys.executable, str(CHECKER), str(stats_path), "--threshold", threshold],
        capture_output=True,
        text=True,
    )


def test_checker_requires_real_mutants(tmp_path):
    result = _run_checker(tmp_path, {"killed": 0, "timeout": 0, "total": 0, "skipped": 0})
    assert result.returncode != 0
    assert "no executed mutants" in result.stderr.lower()


def test_checker_passes_at_sixty_percent_excluding_timeouts(tmp_path):
    # 6 killed, 4 survived, 1 timeout. Timeouts are reported separately and do
    # not get counted as killed, so the trusted score is exactly 60%.
    result = _run_checker(
        tmp_path,
        {"killed": 6, "survived": 4, "timeout": 1, "total": 11, "skipped": 0},
    )
    assert result.returncode == 0
    assert "score=60.00%" in result.stdout
    assert "timeout=1" in result.stdout


def test_checker_fails_below_threshold(tmp_path):
    result = _run_checker(
        tmp_path,
        {"killed": 5, "survived": 5, "timeout": 0, "total": 10, "skipped": 0},
    )
    assert result.returncode != 0
    assert "below threshold" in result.stderr.lower()


def test_checker_derives_survivors_when_export_omits_field(tmp_path):
    # mutmut's export has historically exposed killed/timeout/total/skipped.
    # Derive survivors conservatively instead of treating timeout as killed.
    result = _run_checker(
        tmp_path,
        {"killed": 6, "timeout": 1, "total": 11, "skipped": 0},
    )
    assert result.returncode == 0
    assert "survived=4" in result.stdout


def test_checker_rejects_blocking_threshold_below_sixty(tmp_path):
    result = _run_checker(
        tmp_path,
        {"killed": 10, "survived": 0, "timeout": 0, "total": 10, "skipped": 0},
        threshold="59",
    )
    assert result.returncode != 0
    assert "at least 60" in result.stderr.lower()
