#!/usr/bin/env python3
"""Compute and publish one merge-gate check for each open PR.

Green requires every present check to be successful, every expected check to
come from a trusted workflow or app, every review thread resolved, no reviewer
with outstanding changes requested, and a fresh human approval on the head SHA.

Branch protection still has to require the check; see docs/MERGE_GATE.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

CHECK_NAME = "merge-gate"
ALLOWED_CONCLUSIONS = frozenset({"success", "skipped"})
API_ROOT = "https://api.github.com"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
RUN_RE = re.compile(r"/actions/runs/(\d+)/job/")

CI = ".github/workflows/ci.yml"
EXPECTED_SOURCES = {
    "Validate PR title": ("workflow", (".github/workflows/pr-title.yml",)),
    "required-pr-sections": ("workflow", (".github/workflows/pr-body-check.yml",)),
    "proof": ("workflow", (".github/workflows/stronsium-proof.yml",)),
    "credential-guard": ("workflow", (CI,)),
    "doc-and-manifest-lint": ("workflow", (CI,)),
    "detect": ("workflow", (CI,)),
    "plugin-migration-guard": ("workflow", (CI,)),
    "secret-scan": ("workflow", (CI,)),
    "dependency-review": ("workflow", (".github/workflows/dependency-review.yml",)),
    "Analyze (actions)": ("workflow", (".github/workflows/codeql.yml",)),
    "Analyze (python)": ("workflow", (".github/workflows/codeql.yml",)),
    "e2e-detect": ("workflow", (".github/workflows/e2e.yml",)),
    "label": ("workflow", (".github/workflows/labeler.yml",)),
    "build (3.11)": ("workflow", (".github/workflows/pylint.yml", ".github/workflows/python-package.yml")),
    "build (3.14)": ("workflow", (".github/workflows/pylint.yml", ".github/workflows/python-package.yml")),
    "SonarCloud Code Analysis": ("app", "sonarqubecloud"),
    "Kilo Code Review": ("app", "kilo-code-bot"),
    "Sourcery review": ("app", "sourcery-ai"),
}
THREADS_QUERY = """
query($owner:String!,$name:String!,$number:Int!,$after:String){
  repository(owner:$owner,name:$name){pullRequest(number:$number){
    reviewThreads(first:100,after:$after){
      nodes{id isResolved isOutdated path}
      pageInfo{hasNextPage endCursor}
    }
  }}
}
"""


class GateError(RuntimeError):
    """Raised for unrecoverable API or validation failures."""


def api_headers() -> dict[str, str]:
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        raise GateError("GH_TOKEN is missing")
    return {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "stellarium-merge-gate",
    }


def api_request(method: str, path: str, payload: object = None) -> object:
    if not path.startswith("/"):
        raise GateError("API path must be absolute")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(API_ROOT + path, data=data, headers=api_headers(), method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise GateError("GitHub API " + str(exc.code) + ": " + detail) from exc
    except urllib.error.URLError as exc:
        raise GateError("GitHub API unavailable: " + str(exc.reason)) from exc
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def api_pages(path: str, key: str) -> list[dict]:
    result: list[dict] = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        response = api_request("GET", path + separator + "per_page=100&page=" + str(page))
        if isinstance(response, list):
            items = response
        elif isinstance(response, dict) and isinstance(response.get(key), list):
            items = response[key]
        else:
            raise GateError("unexpected API response for " + key)
        result.extend(item for item in items if isinstance(item, dict))
        if len(items) < 100:
            return result
        page += 1


def repo() -> str:
    value = os.environ.get("GITHUB_REPOSITORY", "")
    if not REPO_RE.fullmatch(value):
        raise GateError("GITHUB_REPOSITORY is missing or invalid")
    return value


def repo_path(suffix: str) -> str:
    return "/repos/" + repo() + suffix


def load_pr(number: int) -> dict:
    if number <= 0:
        raise GateError("invalid PR number")
    pr = api_request("GET", repo_path("/pulls/" + str(number)))
    if not isinstance(pr, dict):
        raise GateError("unexpected PR payload")
    return pr


def load_checks(head_sha: str) -> list[dict]:
    if not SHA_RE.fullmatch(head_sha):
        raise GateError("invalid head SHA")
    checks = api_pages(repo_path("/commits/" + head_sha + "/check-runs"), "check_runs")
    return [item for item in checks if item.get("name") != CHECK_NAME]


def load_threads(number: int) -> list[dict]:
    owner, name = repo().split("/", 1)
    nodes: list[dict] = []
    after = None
    while True:
        variables = {"owner": owner, "name": name, "number": number, "after": after}
        response = api_request("POST", "/graphql", {"query": THREADS_QUERY, "variables": variables})
        pull = response.get("data", {}).get("repository", {}).get("pullRequest") or {}
        threads = pull.get("reviewThreads") or {}
        nodes.extend(node for node in threads.get("nodes", []) if isinstance(node, dict))
        info = threads.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            return nodes
        after = info.get("endCursor")


def load_reviews(number: int) -> list[dict]:
    return api_pages(repo_path("/pulls/" + str(number) + "/reviews"), "reviews")


def load_workflow_path(run_id: str, cache: dict[str, str]) -> str:
    if run_id in cache:
        return cache[run_id]
    if not run_id.isdigit():
        return ""
    response = api_request("GET", repo_path("/actions/runs/" + run_id))
    path = response.get("path", "") if isinstance(response, dict) else ""
    cache[run_id] = path if isinstance(path, str) else ""
    return cache[run_id]


def check_trusted(check: dict, cache: dict[str, str], workflows: dict[str, str] | None = None) -> bool:
    name = str(check.get("name") or "")
    source = EXPECTED_SOURCES.get(name)
    if source is None:
        return False
    kind, value = source
    if kind == "app":
        return (check.get("app") or {}).get("slug") == value
    detail = str(check.get("details_url") or "")
    match = RUN_RE.search(detail)
    if not match:
        return False
    if workflows is not None:
        return workflows.get(match.group(1), "") in value
    return load_workflow_path(match.group(1), cache) in value


def latest_review_states(reviews: list[dict]) -> dict[str, tuple[str, str]]:
    states: dict[str, tuple[str, str]] = {}
    for review in sorted(reviews, key=lambda item: item.get("submitted_at") or ""):
        user = review.get("user") or {}
        login = user.get("login")
        state = review.get("state")
        commit = review.get("commit_id")
        if not isinstance(login, str) or not isinstance(state, str) or not isinstance(commit, str):
            continue
        if state == "DISMISSED":
            states.pop(login, None)
        else:
            states[login] = (state, commit)
    return states


def is_bot(user: dict) -> bool:
    return user.get("type") == "Bot" or str(user.get("login") or "").endswith("[bot]")


def evaluate(pr: dict, checks: list[dict], threads: list[dict], reviews: list[dict],
             workflows: dict[str, str] | None = None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    head_sha = (pr.get("head") or {}).get("sha")

    if pr.get("draft"):
        reasons.append("PR is a draft")
    if pr.get("mergeable") is None:
        reasons.append("mergeability not computed yet")
    elif pr.get("mergeable") is not True:
        reasons.append("PR has a merge conflict")

    trusted_cache: dict[str, str] = {}
    for check in checks:
        name = str(check.get("name") or "unnamed")
        status = check.get("status")
        conclusion = check.get("conclusion")
        if status != "completed" or conclusion not in ALLOWED_CONCLUSIONS:
            reasons.append(f"check {name}: status={status}, conclusion={conclusion}")

    for expected in EXPECTED_SOURCES:
        matches = [item for item in checks if item.get("name") == expected]
        if not matches:
            reasons.append("missing check: " + expected)
        elif not any(item.get("status") == "completed"
                     and item.get("conclusion") in ALLOWED_CONCLUSIONS
                     and check_trusted(item, trusted_cache, workflows) for item in matches):
            reasons.append("untrusted or unsuccessful check: " + expected)

    for thread in threads:
        if thread.get("isResolved") is not True:
            reasons.append("unresolved review thread: " + str(thread.get("path") or thread.get("id")))

    author = (pr.get("user") or {}).get("login")
    states = latest_review_states(reviews)
    for login, (state, _commit) in states.items():
        if state == "CHANGES_REQUESTED":
            reasons.append("changes requested by " + login)
    approvals = 0
    for login, (state, commit) in states.items():
        if state != "APPROVED" or commit != head_sha or login == author:
            continue
        user = next((item.get("user") or {} for item in reviews
                     if (item.get("user") or {}).get("login") == login), {})
        if not is_bot(user):
            approvals += 1
    if approvals == 0:
        reasons.append("no human approval on the current head commit")

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
        "output": {"title": "Merge gate: " + ("green" if ok else "blocked"), "summary": summary},
    }
    api_request("POST", repo_path("/check-runs"), payload)


def targets() -> list[int]:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "schedule":
        pulls = api_pages(repo_path("/pulls?state=open"), "pulls")
        return [item["number"] for item in pulls if isinstance(item.get("number"), int)]
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if event == "workflow_run" and (data.get("workflow_run") or {}).get("name") == "merge gate":
        return []
    if event == "check_run":
        prs = (data.get("check_run") or {}).get("pull_requests") or []
        return [item["number"] for item in prs if isinstance(item, dict) and isinstance(item.get("number"), int)]
    if event == "workflow_run":
        prs = (data.get("workflow_run") or {}).get("pull_requests") or []
        return [item["number"] for item in prs if isinstance(item, dict) and isinstance(item.get("number"), int)]
    pr = data.get("pull_request")
    if isinstance(pr, dict) and isinstance(pr.get("number"), int):
        return [pr["number"]]
    return []


def run_one(number: int) -> bool:
    pr = load_pr(number)
    if pr.get("state") != "open":
        return True
    head_sha = (pr.get("head") or {}).get("sha")
    if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
        raise GateError("PR has no valid head SHA")
    ok, reasons = evaluate(pr, load_checks(head_sha), load_threads(number), load_reviews(number))
    publish(head_sha, ok, reasons, str(pr.get("html_url") or ""))
    print("PR #" + str(number) + ": " + ("green" if ok else "blocked: " + "; ".join(reasons)))
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
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("::error::" + str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
