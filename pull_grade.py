#!/usr/bin/env python3
"""
Pull GitHub Classroom autograding scores from GitHub Actions logs.

Example:

  export GITHUB_AUTH_TOKEN=ghp_xxx

  python3 pull_grade.py \
    --students classroom_roster.csv \
    --output lab1_scores.csv \
    --verbose
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import re
import sys
import time
import zipfile
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


ORG = "UCR-CS153"
ASSIGNMENT_REPO_PREFIX = "lab1-student"
API_URL_BASE = "https://api.github.com"
DEFAULT_PER_PAGE = 100

# GitHub Classroom autograding usually prints:
#   Your score: 85
#   Your score: 85.0
SCORE_RE = re.compile(r"Your score:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def github_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-classroom-grade-puller",
    }


def safe_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    *,
    expected_status: Iterable[int] = (200,),
    retries: int = 3,
    timeout: int = 30,
    **kwargs: Any,
) -> requests.Response:
    expected = set(expected_status)
    last_response: Optional[requests.Response] = None

    for attempt in range(1, retries + 1):
        logging.debug("HTTP %s %s attempt=%d/%d", method, url, attempt, retries)

        try:
            response = session.request(method, url, timeout=timeout, **kwargs)
            last_response = response
        except requests.RequestException as exc:
            logging.warning("Network error: %s", exc)
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
                continue
            raise

        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")

        logging.debug(
            "HTTP response status=%s rate_remaining=%s rate_reset=%s",
            response.status_code,
            remaining,
            reset,
        )

        if response.status_code in expected:
            return response

        if response.status_code in {403, 429, 500, 502, 503, 504} and attempt < retries:
            wait = 2 ** (attempt - 1)

            if response.status_code == 403 and remaining == "0" and reset:
                try:
                    wait = max(wait, int(reset) - int(time.time()) + 5)
                except ValueError:
                    pass

            logging.warning(
                "GitHub API returned %s. Retrying in %ss. body=%s",
                response.status_code,
                wait,
                response.text[:500],
            )
            time.sleep(wait)
            continue

        break

    assert last_response is not None

    body = last_response.text[:1000]
    raise RuntimeError(
        f"GitHub API request failed: {method} {url} "
        f"status={last_response.status_code} body={body}"
    )


def read_students_csv(path: str) -> List[Dict[str, str]]:
    students: List[Dict[str, str]] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {"identifier", "github_username"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Students CSV is missing required columns: {sorted(missing)}. "
                f"Required columns: identifier, github_username"
            )

        for row_num, row in enumerate(reader, start=2):
            ucr_netid = (row.get("identifier") or "").strip()
            github_username = (row.get("github_username") or "").strip()

            if not ucr_netid or not github_username:
                logging.warning(
                    "Skipping row=%d because identifier or github_username is empty: %s",
                    row_num,
                    row,
                )
                continue

            students.append(
                {
                    "UCR_NetID": ucr_netid,
                    "github_username": github_username,
                }
            )

    logging.info("Loaded %d students from %s", len(students), path)
    return students


def repo_name_for_student(github_username: str) -> str:
    return f"{ASSIGNMENT_REPO_PREFIX}-{github_username}"


def repo_url_for_student(github_username: str) -> str:
    return f"https://github.com/{ORG}/{repo_name_for_student(github_username)}.git"


def list_workflow_runs(
    session: requests.Session,
    repo: str,
    per_page: int,
) -> List[Dict[str, Any]]:
    runs: List[Dict[str, Any]] = []
    page = 1

    while True:
        url = (
            f"{API_URL_BASE}/repos/{ORG}/{repo}/actions/runs"
            f"?per_page={per_page}&page={page}"
        )

        response = request_with_retry(session, "GET", url)
        data = safe_json(response)

        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected workflow response for repo={repo}: {data}")

        page_runs = data.get("workflow_runs", [])
        if not page_runs:
            break

        runs.extend(page_runs)

        logging.debug(
            "Repo=%s workflow page=%d runs_on_page=%d total_runs_so_far=%d",
            repo,
            page,
            len(page_runs),
            len(runs),
        )

        page += 1

    return runs


def download_run_log_zip(session: requests.Session, repo: str, run_id: int) -> bytes:
    url = f"{API_URL_BASE}/repos/{ORG}/{repo}/actions/runs/{run_id}/logs"

    # GitHub returns a zip or redirects to a temporary zip URL.
    response = request_with_retry(
        session,
        "GET",
        url,
        expected_status=(200, 302),
        timeout=60,
    )

    logging.debug(
        "Downloaded log zip repo=%s run_id=%s bytes=%d",
        repo,
        run_id,
        len(response.content),
    )

    return response.content


def extract_score_from_zip(zip_bytes: bytes) -> Tuple[Optional[float], Optional[str], List[str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
            names = zip_file.namelist()

            logging.debug("Log zip contains %d files: %s", len(names), names)

            candidate_names: List[str] = []

            # Prefer likely GitHub Classroom autograding logs first.
            candidate_names.extend(
                name
                for name in names
                if "autograding" in name.lower()
                or "educationautograding" in name.lower()
                or "github classroom" in name.lower()
            )

            # Fallback: scan every .txt / .log file.
            candidate_names.extend(
                name
                for name in names
                if name.endswith((".txt", ".log"))
            )

            # Final fallback: scan every file.
            candidate_names.extend(names)

            # Deduplicate while preserving order.
            seen = set()
            candidate_names = [
                name for name in candidate_names
                if not (name in seen or seen.add(name))
            ]

            for name in candidate_names:
                try:
                    raw = zip_file.read(name)
                except KeyError:
                    continue

                text = raw.decode("utf-8", errors="replace")
                match = SCORE_RE.search(text)

                if match:
                    score = float(match.group(1))
                    return score, name, names

            return None, None, names

    except zipfile.BadZipFile:
        logging.error(
            "Downloaded workflow logs are not a valid zip file. First 200 bytes: %r",
            zip_bytes[:200],
        )
        return None, None, []


def score_student(
    session: requests.Session,
    github_username: str,
    ucr_netid: str,
    per_page: int,
) -> Dict[str, Any]:
    repo = repo_name_for_student(github_username)
    repo_url = repo_url_for_student(github_username)

    base_row: Dict[str, Any] = {
        "repo_URL": repo_url,
        "github_username": github_username,
        "UCR_NetID": ucr_netid,
        "status": "",
        "error": "",
        "created_at": "",
        "updated_at": "",
        "score": "",
    }

    logging.info("Processing student=%s netid=%s repo=%s", github_username, ucr_netid, repo)

    try:
        runs = list_workflow_runs(session, repo, per_page)
    except Exception as exc:
        logging.exception("Failed to list workflow runs for repo=%s", repo)
        base_row["status"] = "error"
        base_row["error"] = f"list_workflow_runs failed: {exc}"
        return base_row

    if not runs:
        logging.warning("No workflow runs found for repo=%s", repo)
        base_row["status"] = "no_workflow_runs"
        base_row["error"] = "no workflow runs found"
        return base_row

    logging.info("Found %d workflow runs for repo=%s. Checking all runs for highest score.", len(runs), repo)

    best_score: Optional[float] = None
    best_run: Optional[Dict[str, Any]] = None
    best_log_file: Optional[str] = None

    errors: List[str] = []
    checked_completed_runs = 0

    for index, run in enumerate(runs, start=1):
        run_id = run.get("id")
        status = run.get("status")
        conclusion = run.get("conclusion")
        created_at = run.get("created_at")
        updated_at = run.get("updated_at")

        logging.info(
            "Repo=%s run=%d/%d run_id=%s status=%s conclusion=%s created_at=%s",
            repo,
            index,
            len(runs),
            run_id,
            status,
            conclusion,
            created_at,
        )

        if status != "completed":
            msg = f"run_id={run_id} skipped because workflow status={status}"
            logging.warning("%s", msg)
            errors.append(msg)
            continue

        checked_completed_runs += 1

        try:
            zip_bytes = download_run_log_zip(session, repo, int(run_id))
            score, log_file, log_names = extract_score_from_zip(zip_bytes)

            if score is None:
                msg = f"run_id={run_id} score not found; first_logs={log_names[:5]}"
                logging.warning("Repo=%s %s", repo, msg)
                errors.append(msg)
                continue

            logging.info(
                "Repo=%s run_id=%s score=%s log_file=%s",
                repo,
                run_id,
                score,
                log_file,
            )

            if best_score is None or score > best_score:
                best_score = score
                best_run = run
                best_log_file = log_file
                logging.info(
                    "Repo=%s new best score=%s run_id=%s",
                    repo,
                    best_score,
                    run_id,
                )

        except Exception as exc:
            logging.exception("Failed to process logs repo=%s run_id=%s", repo, run_id)
            errors.append(f"run_id={run_id} log processing failed: {exc}")

    if best_score is not None and best_run is not None:
        base_row["status"] = "graded"
        base_row["error"] = ""
        base_row["created_at"] = best_run.get("created_at") or ""
        base_row["updated_at"] = best_run.get("updated_at") or ""
        base_row["score"] = best_score

        logging.info(
            "Finished repo=%s best_score=%s best_run_id=%s best_log_file=%s",
            repo,
            best_score,
            best_run.get("id"),
            best_log_file,
        )

        return base_row

    base_row["status"] = "error"

    if checked_completed_runs == 0:
        base_row["error"] = "no completed workflow runs; " + " | ".join(errors[:5])
    else:
        base_row["error"] = "no score found in completed workflow runs; " + " | ".join(errors[:5])

    logging.warning(
        "Finished repo=%s without score. checked_completed_runs=%d error=%s",
        repo,
        checked_completed_runs,
        base_row["error"],
    )

    return base_row


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "repo_URL",
        "github_username",
        "UCR_NetID",
        "status",
        "error",
        "created_at",
        "updated_at",
        "score",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logging.info("Wrote output CSV: %s rows=%d", path, len(rows))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pull highest GitHub Classroom autograding score from all Actions workflow runs."
    )

    parser.add_argument(
        "--students",
        required=True,
        help="Students CSV path. Must contain columns: identifier, github_username. identifier is UCR_NetID.",
    )

    parser.add_argument(
        "--output",
        default="scores.csv",
        help="Output CSV path.",
    )

    parser.add_argument(
        "--token-env",
        default="GITHUB_AUTH_TOKEN",
        help="Environment variable containing GitHub token.",
    )

    parser.add_argument(
        "--per-page",
        type=int,
        default=DEFAULT_PER_PAGE,
        help="GitHub API pagination size.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed DEBUG logs.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    token = os.environ.get(args.token_env)
    if not token:
        logging.error("Missing GitHub token. Set it with: export %s=YOUR_TOKEN", args.token_env)
        return 2

    try:
        students = read_students_csv(args.students)
    except Exception as exc:
        logging.exception("Failed to read students CSV")
        print(f"Failed to read students CSV: {exc}", file=sys.stderr)
        return 2

    if not students:
        logging.error("No valid students found in %s", args.students)
        return 2

    session = requests.Session()
    session.headers.update(github_headers(token))

    rows: List[Dict[str, Any]] = []

    for index, student in enumerate(students, start=1):
        logging.info(
            "[%d/%d] Start grading github_username=%s UCR_NetID=%s",
            index,
            len(students),
            student["github_username"],
            student["UCR_NetID"],
        )

        row = score_student(
            session=session,
            github_username=student["github_username"],
            ucr_netid=student["UCR_NetID"],
            per_page=args.per_page,
        )

        rows.append(row)

        logging.info(
            "[%d/%d] Done github_username=%s status=%s score=%s error=%s",
            index,
            len(students),
            row["github_username"],
            row["status"],
            row["score"],
            row["error"],
        )

    write_csv(args.output, rows)

    graded = sum(1 for row in rows if row["status"] == "graded")
    errors = sum(1 for row in rows if row["status"] != "graded")

    logging.info("All done. graded=%d errors=%d output=%s", graded, errors, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
