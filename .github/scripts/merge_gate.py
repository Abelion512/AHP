#!/usr/bin/env python3
"""Compute and publish a single merge-gate check for each open PR.

The check is green only when every applicable check run is green, every review
thread is resolved, no human review requested changes, and at least one human
approval exists. It publishes a check run named 'merge-gate' on the PR head.

Branch protection still has to require that check; see docs/MERGE_GATE.md.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CHECK_NAME = "merge-gate"
SUCCESS_CONCLUSIONS = frozenset({"success", "skipped", "neutral"})
EXPECTED_CHECKS = (
    "Validate PR title", "required-pr-sections", "proof", "credential-guard",
    "doc-and-manifest-lint", "dependency-review", "detect", "Analyze (actions)",
    "Analyze (python)", "CodeQL", "SonarCloud Code Analysis", "Kilo Code Review",
    "Sourcery review", "Real Hermes E2E", "e2e-detect", "plugin-migration-guard",
    "secret-scan", "label", "build (3.11)", "build (3.14)",
)
THREADS_QUERY = """
query($owner:String!,$name:String!,$number:Int!){
  repository(owner:$owner,name:$name){pullRequest(number:$number){
    reviewThreads(first:100){nodes{id isResolved isOutdated path}}
  }}
}
"""


def gh(args: list[str], jq: str | None = None, paginate: bool = False) -> list[object]:
    # Fixed prefixes only: endpoint paths are built in this module, never taken
    # from CLI, PR text or model output. Inputs are passed as typed -F values.
    allowed = {
        "graphql", "repos/", "pulls/"
    }
    if not args or not any(args[0].startswith(prefix) for prefix in allowed):
        raise ValueError("unsupported gh api endpoint")
    cmd = ["gh", "api", *args]
    if jq:
        cmd.extend(["--jq", jq])
    if paginate:
        cmd.append("--paginate")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gh api failed")
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def gh_one(args: list[str]) -> object:
    items = gh(args)
    if not items:
        raise RuntimeError("empty gh api response")
    return items[0]


def repo() -> str:
    value = os.environ.get("GITHUB_REPOSITORY", "")
    if not value or "/" not in value:
        raise RuntimeError("GITHUB_REPOSITORY is missing")
    return value


def load_pr(number: int) -> dict:
    pr = gh_one(["repos/" + repo() + "/pulls/" + str(number)])
    if not isinstance(pr, dict):
        raise RuntimeError("unexpected PR payload")
    return pr


def load_checks(head_sha: str) -> list[dict]:
    result = gh(["repos/" + repo() + "/commits/" + head_sha + "/check-runs?per_page=100",
                 "--jq", ".check_runs[] | @json"], paginate=True)
    return [item for item in result if isinstance(item, dict) and item.get("name") != CHECK_NAME]


def load_threads(number: int) -> list[dict]:
    owner, name = repo().split("/", 1)
    result = gh_one(["graphql", "-f", "query=" + THREADS_QUERY,
                     "-F", "owner=" + owner, "-F", "name=" + name, "-F", "number=" + str(number)])
    pull = result.get("data", {}).get("repository", {}).get("pullRequest") or {}
    nodes = pull.get("reviewThreads", {}).get("nodes") or []
    return [node for node in nodes if isinstance(node, dict)]


def load_reviews(number: int) -> list[dict]:
    result = gh(["repos/" + repo() + "/pulls/" + str(number) + "/reviews?per_page=100",
                 "--jq", ".[] | @json"], paginate=True)
    return [item for item in result if isinstance(item, dict)]


def latest_review_states(reviews: list[dict]) -> dict[str, str]:
    states: dict[str, str] = {}
    for review in sorted(reviews, key=lambda item: item.get("submitted_at") or ""):
        user = review.get("user") or {}
        login = user.get("login")
        state = review.get("state")
        if not isinstance(login, str) or not isinstance(state, str):
            continue
        if state == "DISMISSED":
            states.pop(login, None)
        else:
            states[login] = state
    return states


def evaluate(pr: dict, checks: list[dict], threads: list[dict], reviews: list[dict]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if pr.get("draft"):
        reasons.append("PR is a draft")
    if pr.get("mergeable") is not True:
        reasons.append("PR has a merge conflict or mergeability is unknown")

    for check in checks:
        name = str(check.get("name") or "unnamed")
        status = check.get("status")
        conclusion = check.get("conclusion")
        if status != "completed" or conclusion not in SUCCESS_CONCLUSIONS:
            reasons.append(f"check {name}: status={status}, conclusion={conclusion}")

    names = [str(check.get("name") or "") for check in checks]
    for expected in EXPECTED_CHECKS:
        if not any(name == expected or name.startswith(expected + " (") for name in names):
            reasons.append(f"missing check: {expected}")

    for thread in threads:
        if thread.get("isResolved") is not True:
            reasons.append(f"unresolved review thread: {thread.get('path') or thread.get('id')}")

    author = (pr.get("user") or {}).get("login")
    states = latest_review_states(reviews)
    for login, state in states.items():
        if state == "CHANGES_REQUESTED":
            reasons.append(f"changes requested by {login}")
    approvals = [login for login, state in states.items()
                 if state == "APPROVED" and not login.endswith("[bot]") and login != author]
    if not approvals:
        reasons.append("no human approval")

    return not reasons, reasons


def publish(head_sha: str, ok: bool, reasons: list[str], details_url: str) -> None:
    summary = "All checks, comments and approvals are green.\n" if ok else \
        "Merge gate is not green:\n" + "".join("- " + reason + "\n" for reason in reasons)
    payload = {
        "name": CHECK_NAME,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": "success" if ok else "failure",
        "details_url": details_url,
        "output": {
            "title": "Merge gate: " + ("green" if ok else "blocked"),
            "summary": summary,
        },
    }
    result = subprocess.run(
        ["gh", "api", "-X", "POST", "repos/" + repo() + "/check-runs", "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "could not publish check run")


def targets() -> list[int]:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "schedule":
        result = gh(["repos/" + repo() + "/pulls?state=open&per_page=100", "--jq", ".[] | @json"],
                    paginate=True)
        return [item["number"] for item in result if isinstance(item, dict) and isinstance(item.get("number"), int)]
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if event == "workflow_run":
        if (data.get("workflow_run") or {}).get("name") == "merge gate":
            return []
        return [item["number"] for item in (data.get("workflow_run") or {}).get("pull_requests", [])
                if isinstance(item, dict) and isinstance(item.get("number"), int)]
    pr = data.get("pull_request")
    if isinstance(pr, dict) and isinstance(pr.get("number"), int):
        return [pr["number"]]
    return []


def run_one(number: int) -> bool:
    pr = load_pr(number)
    if pr.get("state") != "open":
        return True
    head_sha = (pr.get("head") or {}).get("sha")
    if not isinstance(head_sha, str) or not head_sha:
        raise RuntimeError("PR has no head SHA")
    ok, reasons = evaluate(pr, load_checks(head_sha), load_threads(number), load_reviews(number))
    publish(head_sha, ok, reasons, str(pr.get("html_url") or ""))
    print(f"PR #{number}: " + ("green" if ok else "blocked: " + "; ".join(reasons)))
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", nargs="?", type=int, help="single PR number")
    parser.add_argument("--auto", action="store_true", help="derive PRs from the GitHub event")
    parser.add_argument("--targets", action="store_true", help="print derived PR numbers as JSON")
    args = parser.parse_args(argv)
    try:
        if args.targets:
            print(json.dumps(targets()))
            return 0
        numbers = [args.pr] if args.pr else targets() if args.auto else []
        for number in numbers:
            run_one(number)
        return 0
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("::error::" + str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
