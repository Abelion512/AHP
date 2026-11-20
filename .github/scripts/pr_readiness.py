"""Read-only PR readiness gate: CI, review threads and reviews.

Run after `gh pr create`. Exit 0 means the PR is ready for human review and
merge; any failed or pending check, unresolved thread, changes-requested
review, truncated query, or non-mergeable state exits 1. Human approval is
reported separately because the agent cannot approve its own PR.
"""
import json
import os
import re
import subprocess
import sys

QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      number
      state
      isDraft
      mergeable
      mergeStateStatus
      reviewDecision
      headRefOid
      commits(last:1) {
        nodes { commit { statusCheckRollup { contexts(first:100) {
          pageInfo { hasNextPage }
          nodes {
            ... on CheckRun { name status conclusion createdAt: startedAt checkSuite { app { id } } }
            ... on StatusContext { name: context status: state conclusion: state createdAt }
          }
        } } } }
      }
      reviewThreads(first:100) {
        pageInfo { hasNextPage }
        nodes { isResolved comments(first:1) { nodes { author { login } } } }
      }
      reviews(last:20) {
        pageInfo { hasNextPage hasPreviousPage }
        nodes { author { login } state submittedAt }
      }
    }
  }
}
"""
FAILURES = {"FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "CANCELLED",
            "STARTUP_FAILURE", "STALE"}
STATUS_STATES = {"SUCCESS": "SUCCESS", "FAILURE": "FAILURE",
                 "ERROR": "FAILURE", "PENDING": None}


def gh_call(*args):
    try:
        return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        raise


def repo_name():
    return os.environ.get("GH_REPO") or gh_call(
        "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()


def fetch(number):
    owner, name = repo_name().split("/", 1)
    raw = gh_call("api", "graphql", "-f", "query=" + QUERY,
                  "-F", "owner=" + owner, "-F", "name=" + name, "-F", "number=" + str(number))
    return json.loads(raw)["data"]["repository"]["pullRequest"]


def normalize(check):
    status = check.get("status")
    if status in STATUS_STATES:
        conclusion = STATUS_STATES[status]
        return {"name": check.get("name") or "unnamed", "status": "COMPLETED" if conclusion else "IN_PROGRESS",
                "conclusion": conclusion, "app": "status"}
    app = ((check.get("checkSuite") or {}).get("app") or {}).get("id") or "unknown"
    return {"name": check.get("name") or "unnamed", "status": status,
            "conclusion": check.get("conclusion"), "app": app}


def author_login(node):
    return ((node or {}).get("author") or {}).get("login") or "unknown"


def summary(pr):
    commits = (pr.get("commits") or {}).get("nodes") or []
    commit = (commits[0].get("commit") or {}) if commits else {}
    rollup = commit.get("statusCheckRollup") or {}
    contexts = rollup.get("contexts") or {}
    reviews = pr.get("reviews") or {}
    truncated = any(bool((node or {}).get("pageInfo", {}).get("hasNextPage"))
                    for node in (contexts, pr.get("reviewThreads"))) or bool(
        reviews.get("pageInfo", {}).get("hasPreviousPage"))

    latest = {}
    for check in contexts.get("nodes") or []:
        item = normalize(check)
        key = (item["name"], item["app"])
        stamp = check.get("createdAt") or ""
        if key not in latest or stamp > latest[key][0]:
            latest[key] = (stamp, item)
    runs = [item for _, item in latest.values()]
    passed = [r["name"] for r in runs
              if r["status"] == "COMPLETED" and r["conclusion"]
              and r["conclusion"] not in FAILURES]
    failed = [r["name"] for r in runs
              if r["status"] == "COMPLETED" and r["conclusion"] in FAILURES]
    pending = [r["name"] for r in runs
               if r["status"] != "COMPLETED" or not r["conclusion"]]

    threads = (pr.get("reviewThreads") or {}).get("nodes") or []
    unresolved = [
        author_login(((t.get("comments") or {}).get("nodes") or [None])[0])
        for t in threads if not t.get("isResolved")
        and ((t.get("comments") or {}).get("nodes") or [])
    ]

    latest_review = {}
    for review in (pr.get("reviews") or {}).get("nodes") or []:
        author = author_login(review)
        stamp = review.get("submittedAt") or ""
        if author not in latest_review or stamp > latest_review[author][0]:
            latest_review[author] = (stamp, review.get("state"))
    states = {state: [author for author, (_, value) in latest_review.items() if value == state]
              for state in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED")}

    ready = bool(runs) and not (failed or pending or unresolved or truncated
                                or states["CHANGES_REQUESTED"])
    ready = ready and pr.get("state") == "OPEN" and not pr.get("isDraft") \
        and pr.get("mergeable") == "MERGEABLE"
    return {"head": pr.get("headRefOid") or "unknown", "state": pr.get("state") or "UNKNOWN",
            "draft": pr.get("isDraft"), "mergeable": pr.get("mergeable"),
            "decision": pr.get("reviewDecision"), "passed": passed, "failed": failed,
            "pending": pending, "unresolved": unresolved, "reviews": states,
            "truncated": truncated, "ready": ready}


def clean(name):
    return re.sub(r"[\x00-\x1f\x7f]", "?", str(name))[:120]


def report(number, s):
    print(f"PR #{number} readiness (head {clean(s['head'])[:7]}, {clean(s['state'])})")
    print(f"CI: {len(s['passed'])} pass, {len(s['failed'])} fail, {len(s['pending'])} pending")
    for name in s["failed"]:
        print(f"  FAIL {clean(name)}")
    for name in s["pending"]:
        print(f"  PENDING {clean(name)}")
    print(f"Threads: {len(s['unresolved'])} unresolved {[clean(a) for a in s['unresolved']]}")
    for state, authors in s["reviews"].items():
        print(f"Reviews {state}: {len(authors)} {[clean(a) for a in authors]}")
    print(f"Decision: {clean(s['decision'])}")
    print(f"Mergeable: {clean(s['mergeable'])}, draft: {s['draft']}")
    if s["truncated"]:
        print("Truncated query results: narrow the PR or paginate before merging")
    print(f"Human approval: {'present' if s['reviews']['APPROVED'] else 'pending (reviewer step)'}")
    print("READY" if s["ready"] else "NOT READY")
    return 0 if s["ready"] else 1


def main():
    args = sys.argv[1:]
    if not args or not args[0].isdigit() or len(args) > 2:
        print("usage: python3 pr_readiness.py <pr-number> [owner/repo]", file=sys.stderr)
        return 2
    if len(args) == 2:
        os.environ["GH_REPO"] = args[1]
    number = int(args[0])
    return report(number, summary(fetch(number)))


if __name__ == "__main__":
    raise SystemExit(main())
