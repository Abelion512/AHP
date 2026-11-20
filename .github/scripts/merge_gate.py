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
# Workflow checks need a real success: a skipped security/quality check must
# not pass. Kept strict so a failed reevaluation cannot leave a stale green.
# External review apps may skip when they find no findings.
ALLOWED_CONCLUSIONS = frozenset({"success"})
# Backwards-compatible aliases for earlier review/test naming.
SUCCESS_CONCLUSIONS = ALLOWED_CONCLUSIONS
REVIEW_APP_CHECKS = frozenset({
    "Sourcery review", "Kilo Code Review", "SonarCloud Code Analysis", "Socket",
})
# Workflow jobs whose conditions legitimately skip them on some PRs.
SKIPPABLE_CHECKS = frozenset({"label"})
ENFORCED_BASE = "main"
API_ROOT = "https://api.github.com"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
RUN_RE = re.compile(r"/actions/runs/(\d+)/jobs?/")

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
# Backwards-compatible alias for earlier review/test naming.
EXPECTED_CHECKS = tuple(EXPECTED_SOURCES.keys())
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


def valid_sha(value: object) -> str | None:
    return value if isinstance(value, str) and SHA_RE.fullmatch(value) else None


def load_pr(number: int) -> dict:
    if number <= 0:
        raise GateError("invalid PR number")
    pr = api_request("GET", repo_path("/pulls/" + str(number)))
    if not isinstance(pr, dict):
        raise GateError("unexpected PR payload")
    return pr


def load_changed_files(number: int) -> set[str]:
    """Paths a PR changes, so a rewritten trusted workflow cannot self-approve."""
    files = api_pages(repo_path("/pulls/" + str(number) + "/files"), "files")
    return {str(item["filename"]) for item in files if isinstance(item.get("filename"), str)}


def load_checks(head_sha: str) -> list[dict]:
    if not SHA_RE.fullmatch(head_sha):
        raise GateError("invalid head SHA")
    checks = api_pages(repo_path("/commits/" + head_sha + "/check-runs"), "check_runs")
    return [item for item in checks if item.get("name") != CHECK_NAME]


def gate_checks(head_sha: str) -> list[dict]:
    """Existing merge-gate check runs for this head, if any."""
    if not SHA_RE.fullmatch(head_sha):
        raise GateError("invalid head SHA")
    checks = api_pages(repo_path("/commits/" + head_sha + "/check-runs"), "check_runs")
    return [item for item in checks
            if item.get("name") == CHECK_NAME and isinstance(item.get("id"), int)
            and not isinstance(item.get("id"), bool)]


def gate_check_ids(head_sha: str) -> list[int]:
    return [item["id"] for item in gate_checks(head_sha)]


def check_recency(check: dict) -> tuple[str, int, str]:
    attempt = check.get("run_attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool):
        attempt = 0
    started = str(check.get("started_at") or check.get("created_at") or "")
    return (started, attempt, str(check.get("id") or ""))


def check_source(check: dict) -> str:
    """Provenance key. Reruns of one workflow job collapse; distinct sources stay."""
    detail = str(check.get("details_url") or "")
    match = RUN_RE.search(detail)
    if match and (check.get("app") or {}).get("slug") == "github-actions":
        return "run:" + match.group(1)
    return "app:" + str((check.get("app") or {}).get("slug") or check.get("id") or "")


def latest_checks(checks: list[dict]) -> list[dict]:
    """Keep only the newest attempt of each named check and source."""
    latest: dict[tuple[str, str], dict] = {}
    for check in checks:
        key = (str(check.get("name") or ""), check_source(check))
        current = latest.get(key)
        if current is None or check_recency(check) > check_recency(current):
            latest[key] = check
    return list(latest.values())


def load_threads(number: int) -> list[dict]:
    owner, name = repo().split("/", 1)
    nodes: list[dict] = []
    after = None
    while True:
        variables: dict[str, object] = {"owner": owner, "name": name, "number": number}
        if after is not None:
            variables["after"] = after
        response = api_request("POST", "/graphql", {"query": THREADS_QUERY, "variables": variables})
        if not isinstance(response, dict):
            raise GateError("unexpected GraphQL response")
        if response.get("errors"):
            raise GateError("GraphQL errors: " + json.dumps(response["errors"])[:300])
        data = response.get("data")
        repository = data.get("repository") if isinstance(data, dict) else None
        pull = repository.get("pullRequest") if isinstance(repository, dict) else None
        threads = pull.get("reviewThreads") if isinstance(pull, dict) else None
        if not isinstance(threads, dict):
            raise GateError("GraphQL response missing repository or pull request data")
        nodes.extend(node for node in threads.get("nodes", []) if isinstance(node, dict))
        info = threads.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            return nodes
        after = info.get("endCursor")
        if not isinstance(after, str) or not after:
            raise GateError("GraphQL pagination missing endCursor")


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


def check_trusted(check: dict, cache: dict[str, str], workflows: dict[str, str] | None = None,
                  changed_files: frozenset[str] | set[str] = frozenset()) -> bool:
    name = str(check.get("name") or "")
    source = EXPECTED_SOURCES.get(name)
    if source is None:
        return False
    kind, value = source
    app = (check.get("app") or {}).get("slug")
    if kind == "app":
        return app == value
    # A workflow check must come from GitHub Actions, not an app that forged
    # the name and linked to a trusted run in details_url.
    if app != "github-actions":
        return False
    match = RUN_RE.search(str(check.get("details_url") or ""))
    if not match:
        return False
    path = (workflows.get(match.group(1), "") if workflows is not None
            else load_workflow_path(match.group(1), cache))
    # A PR that edits a trusted workflow must not satisfy the gate with it.
    return path in value and path not in changed_files


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


def is_bot(user: object) -> bool:
    if not isinstance(user, dict):
        return False
    return user.get("type") == "Bot" or str(user.get("login") or "").endswith("[bot]")


def conclusion_allowed(check: dict) -> bool:
    """Workflow checks need success; review apps and conditional jobs may skip."""
    conclusion = check.get("conclusion")
    if conclusion in ALLOWED_CONCLUSIONS:
        return True
    if conclusion != "skipped":
        return False
    name = str(check.get("name") or "")
    app = (check.get("app") or {}).get("slug")
    if name in REVIEW_APP_CHECKS:
        return bool(app)
    return name in SKIPPABLE_CHECKS and app == "github-actions"


def evaluate(pr: dict, checks: list[dict], threads: list[dict], reviews: list[dict],
             workflows: dict[str, str] | None = None,
             changed_files: frozenset[str] | set[str] = frozenset()) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    checks = latest_checks(checks)
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
        if status != "completed" or not conclusion_allowed(check):
            reasons.append(f"check {name}: status={status}, conclusion={conclusion}")

    for expected in EXPECTED_SOURCES:
        matches = [item for item in checks if item.get("name") == expected]
        if not matches:
            reasons.append("missing check: " + expected)
        elif not all(item.get("status") == "completed"
                     and conclusion_allowed(item)
                     and check_trusted(item, trusted_cache, workflows, changed_files)
                     for item in matches):
            reasons.append("untrusted or unsuccessful check: " + expected)

    for thread in threads:
        if thread.get("isResolved") is not True:
            reasons.append("unresolved review thread: " + str(thread.get("path") or thread.get("id")))

    author = (pr.get("user") or {}).get("login")
    if not isinstance(author, str) or not author:
        # Without the author login the self-approval exclusion cannot work.
        reasons.append("missing PR author login")
    states = latest_review_states(reviews)
    for login, (state, _commit) in states.items():
        if state == "CHANGES_REQUESTED":
            reasons.append("changes requested by " + login)
    approvals = 0
    for login, (state, commit) in states.items():
        if state != "APPROVED" or commit != head_sha or login == author:
            continue
        matching = [item for item in reviews
                    if (item.get("user") or {}).get("login") == login]
        user = (sorted(matching, key=lambda item: item.get("submitted_at") or "")[-1].get("user")
                if matching else {}) or {}
        if not is_bot(user):
            approvals += 1
    if approvals == 0:
        reasons.append("no human approval on the current head commit")

    return not reasons, reasons


def _put_gate_check(head_sha: str, payload: dict, pr_number: int | None) -> None:
    all_gate_checks = gate_checks(head_sha)
    wanted = "pr-" + str(pr_number) if pr_number is not None else None
    existing = ([item for item in all_gate_checks if item.get("external_id") == wanted]
                if wanted is not None else all_gate_checks)
    if not existing and wanted is not None:
        # Adopt an older unkeyed check instead of piling up same-name runs.
        existing = [item for item in all_gate_checks if not item.get("external_id")][:1]
    if existing:
        for check in existing:
            api_request("PATCH", repo_path("/check-runs/" + str(check["id"])), payload)
    else:
        api_request("POST", repo_path("/check-runs"), payload)


def publish(head_sha: str, ok: bool, reasons: list[str], details_url: str,
            pr_number: int | None = None) -> None:
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
    if pr_number is not None:
        payload["external_id"] = "pr-" + str(pr_number)
    _put_gate_check(head_sha, payload, pr_number)


def publish_pending(head_sha: str, pr_number: int, details_url: str) -> None:
    """Mark the check pending first so a cancelled run cannot leave a stale green."""
    _put_gate_check(head_sha, {
        "name": CHECK_NAME,
        "head_sha": head_sha,
        "status": "in_progress",
        "details_url": details_url,
        "external_id": "pr-" + str(pr_number),
        "output": {"title": "Merge gate: evaluating",
                   "summary": "Merge gate is evaluating this PR.\n"},
    }, pr_number)


def publish_blocking(head_sha: str, reason: str, pr_number: int | None = None) -> None:
    """Retract an earlier green so a failed read cannot leave a stale gate."""
    try:
        publish(head_sha, False, [reason], "", pr_number)
        return
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        # Listing check runs can fail independently of writing them. Retry the
        # failure result as a fresh POST so the stale green is no longer the
        # only result for this head SHA.
        print("::warning::could not update merge gate check: " + str(exc))
    payload = {
        "name": CHECK_NAME,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": "failure",
        "output": {"title": "Merge gate: blocked",
                   "summary": "Merge gate is not green:\n- " + reason + "\n"},
    }
    if pr_number is not None:
        payload["external_id"] = "pr-" + str(pr_number)
    try:
        api_request("POST", repo_path("/check-runs"), payload)
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        # Checks API is down too: only the log and the non-zero exit remain.
        print("::error::could not publish blocking merge gate: " + str(exc))


def targets() -> list[tuple[int, str | None]]:
    """PR numbers and head SHAs derived from the current event."""
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "schedule":
        pulls = api_pages(repo_path("/pulls?state=open"), "pulls")
        return [(item["number"], valid_sha((item.get("head") or {}).get("sha")))
                for item in pulls if isinstance(item.get("number"), int)]
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if event == "workflow_run" and (data.get("workflow_run") or {}).get("name") == "merge gate":
        return []
    if event in ("check_run", "workflow_run"):
        run = data.get(event) or {}
        sha = valid_sha(run.get("head_sha"))
        prs = run.get("pull_requests") or []
        return [(item["number"], sha) for item in prs
                if isinstance(item, dict) and isinstance(item.get("number"), int)]
    pr = data.get("pull_request")
    if isinstance(pr, dict) and isinstance(pr.get("number"), int):
        return [(pr["number"], valid_sha((pr.get("head") or {}).get("sha")))]
    return []


def run_one(number: int, known_sha: str | None = None) -> bool:
    try:
        pr = load_pr(number)
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        # A lookup failure must not leave an earlier green for the same head.
        if known_sha:
            publish_blocking(known_sha, "PR lookup failed: " + str(exc), number)
        raise
    if pr.get("state") != "open":
        return True
    base = (pr.get("base") or {}).get("ref")
    if base != ENFORCED_BASE:
        # Required workflows run only for main-targeted PRs; other bases have
        # no enforceable gate, so skip instead of publishing a false failure.
        print("PR #" + str(number) + ": skipped (base " + str(base) + " != " + ENFORCED_BASE + ")")
        return True
    head_sha = valid_sha((pr.get("head") or {}).get("sha"))
    if not head_sha:
        raise GateError("PR has no valid head SHA")
    details_url = str(pr.get("html_url") or "")
    try:
        publish_pending(head_sha, number, details_url)
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        publish_blocking(head_sha, "merge gate could not be marked pending: " + str(exc), number)
        raise
    try:
        ok, reasons = evaluate(pr, load_checks(head_sha), load_threads(number),
                               load_reviews(number), changed_files=load_changed_files(number))
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        publish_blocking(head_sha, "merge gate evaluation failed: " + str(exc), number)
        raise
    try:
        publish(head_sha, ok, reasons, details_url, number)
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        publish_blocking(head_sha, "merge gate publish failed: " + str(exc), number)
        raise
    print("PR #" + str(number) + ": " + ("green" if ok else "blocked: " + "; ".join(reasons)))
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", nargs="?", type=int, help="single PR number")
    parser.add_argument("--auto", action="store_true", help="derive PRs from the GitHub event")
    parser.add_argument("--targets", action="store_true", help="print derived PR numbers as JSON")
    args = parser.parse_args(argv)
    try:
        found = targets() if args.auto else []
        if args.targets:
            print(json.dumps([number for number, _ in found]))
            return 0
        jobs = [(args.pr, None)] if args.pr else found
        failed = False
        for number, known_sha in jobs:
            try:
                run_one(number, known_sha)
            except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
                # One bad PR must not stop a scheduled sweep of the others.
                print("::error::PR #" + str(number) + ": " + str(exc))
                failed = True
        return 2 if failed else 0
    except (GateError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("::error::" + str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
