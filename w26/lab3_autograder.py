#!/usr/bin/env python3
"""
Lab 3 (thread) autograder for CI (e.g. GitHub Actions).

Runs `make grade`, parses MIT gradelib output, maps to course rubric:
  - User-level threads (xv6 uthread): 50 pts max
  - Parallel hash (notxv6/ph):       50 pts max
  - Barrier bonus:                    10 pts max

Exit code: 0 only if total == max total (110); otherwise 1.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# --- Rubric (must sum: 50 + 50 + 10 = 110) ---------------------------------
# Maps grade-lab-thread.py test titles -> (bucket, points if OK)
RUBRIC = {
    "uthread": ("threads", 50),
    # Parallel hash bucket (50)
    "ph_safe": ("hash", 25),
    "ph_fast": ("hash", 25),
    # Bonus
    "barrier": ("bonus", 10),
}

BUCKET_MAX = {"threads": 50, "hash": 50, "bonus": 10}
MAX_TOTAL = sum(BUCKET_MAX.values())  # 110


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def parse_test_results(output: str) -> dict[str, bool | None]:
    """Each key -> True (OK), False (FAIL), None (not seen)."""
    lines = strip_ansi(output).splitlines()
    results: dict[str, bool | None] = {k: None for k in RUBRIC}
    # Lines look like: "uthread: OK (32.0s)", "Timeout! uthread: FAIL (32.0s)", etc.
    title_pat = "|".join(re.escape(t) for t in sorted(RUBRIC.keys(), key=len, reverse=True))
    line_re = re.compile(rf"\b({title_pat}):\s*(OK|FAIL)\b")
    for line in lines:
        m = line_re.search(line)
        if not m:
            continue
        name, status = m.group(1), m.group(2)
        if name in results:
            results[name] = status == "OK"
    return results


def parse_mit_score(output: str) -> tuple[int | None, int | None]:
    m = re.search(r"^Score:\s*(\d+)/(\d+)\s*$", strip_ansi(output), re.MULTILINE)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def compute_score(results: dict[str, bool | None]) -> tuple[int, dict[str, int], list[str]]:
    """Returns (total, per_bucket_scores, error_messages)."""
    bucket_scores = {b: 0 for b in BUCKET_MAX}
    errors: list[str] = []

    for title, ok in results.items():
        bucket, pts = RUBRIC[title]
        if ok is True:
            bucket_scores[bucket] += pts
        elif ok is False:
            errors.append(f"{title}: FAIL (0 / {pts} toward {bucket})")
        else:
            errors.append(f"{title}: no OK/FAIL line in grader output (treated as 0 / {pts})")

    total = sum(bucket_scores.values())
    return total, bucket_scores, errors


def format_breakdown(bucket_scores: dict[str, int]) -> str:
    lines = [
        "Rubric breakdown:",
        f"  User-level threads (max {BUCKET_MAX['threads']}): {bucket_scores['threads']}/{BUCKET_MAX['threads']}",
        f"    - uthread: {RUBRIC['uthread'][1]} pts",
        f"  Parallel hash (max {BUCKET_MAX['hash']}): {bucket_scores['hash']}/{BUCKET_MAX['hash']}",
        f"    - ph_safe: {RUBRIC['ph_safe'][1]} pts  |  ph_fast: {RUBRIC['ph_fast'][1]} pts",
        f"  Barrier bonus (max {BUCKET_MAX['bonus']}): {bucket_scores['bonus']}/{BUCKET_MAX['bonus']}",
    ]
    return "\n".join(lines)


def main() -> int:
    root = Path(__file__).resolve().parent
    os.chdir(root)

    proc = subprocess.run(
        ["make", "grade"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    lines = combined.splitlines()
    last_lines = lines[-80:] if lines else []

    results = parse_test_results(combined)
    final_score, bucket_scores, derived_errors = compute_score(results)
    mit_earned, mit_possible = parse_mit_score(combined)

    print(format_breakdown(bucket_scores))
    print()
    print(f"MIT gradelib Score line (reference): {mit_earned}/{mit_possible}")
    print()

    # No Score line => build failure or grader crashed before summary
    grade_incomplete = mit_earned is None

    if grade_incomplete:
        print("[!] make grade did not complete successfully (build failure, timeout, or missing Score line).")
        if proc.returncode != 0:
            print(f"[!] subprocess exit code: {proc.returncode}")
        print("=======")
        print("Last output:")
        for line in last_lines:
            print(line)
        print("=======")
        print(f"Your score: {final_score} / {MAX_TOTAL}")
        return 1

    if final_score == MAX_TOTAL:
        print("[!] All checks passed!")
        print("=======")
        print(f"Your score: {final_score} / {MAX_TOTAL}")
        return 0

    print("[!] Some lab checks did not pass.")
    print("=======")
    print("Errors:")
    for e in derived_errors[:20]:
        print(f"[!] {e}")
    print("=======")
    print("Last output:")
    for line in last_lines:
        print(line)
    print("=======")
    print(f"Your score: {final_score} / {MAX_TOTAL}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
