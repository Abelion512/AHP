"""Read-only PR readiness gate: CI, review threads and reviews.

Run after `gh pr create`. Exit 0 means the PR is ready for human review and
merge; any failed or pending check, unresolved thread, or changes-requested
review exits 1. Human approval is reported separately because the agent cannot
approve its own PR.
"""
import json
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
        nodes { commit { statusCheckRollup { contexts(first:100) { nodes {
          ... on CheckRun { name status conclusion createdAt: startedAt }
          ... on StatusContext { name: context status: state conclusion: state createdAt }
        } } } } }
      }
      reviewThreads(first:100) {
        nodes { isResolved comments(first:1) { nodes { author { login } } } }
      }
      reviews(last:20) { nodes { author { login } state } }
    }
  }
}
"""
FAILURES = {"FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "CANCELLED", "STARTUP_FAILURE"}


def gh_call(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def repo_name():
    return gh_call("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()


def fetch(number):
    owner, name = repo_name().split("/", 1)
    raw = gh_call("api", "graphql", "-f", "query=" + QUERY,
              "-F", "owner=" + owner, "-F", "name=" + name, "-F", "number=" + str(number))
    return json.loads(raw)["data"]["repository"]["pullRequest"]


STATUS_STATES = {"SUCCESS": "SUCCESS", "FAILURE": "FAILURE",
                 "ERROR": "FAILURE", "PENDING": None}


def normalize(check):
    status = check.get("status")
    if status in STATUS_STATES:
        conclusion = STATUS_STATES[status]
        return {"name": check.get("name") or "unnamed",
                "status": "COMPLETED" if conclusion else "IN_PROGRESS",
                "conclusion": conclusion}
    return {"name": check.get("name") or "unnamed", "status": status,
            "conclusion": check.get("conclusion")}


def author_login(node):
    return ((node or {}).get("author") or {}).get("login") or "unknown"


def summary(pr):
    commits = (pr.get("commits") or {}).get("nodes") or []
    commit = (commits[0].get("commit") or {}) if commits else {}
    rollup = commit.get("statusCheckRollup") or {}
    raw = (rollup.get("contexts") or {}).get("nodes") or []
    latest = {}
    for check in raw:
        name = check.get("name") or "unnamed"
        stamp = check.get("createdAt") or ""
        if name not in latest or stamp > latest[name][0]:
            latest[name] = (stamp, check)
    runs = [normalize(check) for _, check in latest.values()]
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
    reviews = (pr.get("reviews") or {}).get("nodes") or []
    states = {state: [author_login(r) for r in reviews if r.get("state") == state]
              for state in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED")}
    ready = not (failed or pending or unresolved or states["CHANGES_REQUESTED"])
    return {"head": pr.get("headRefOid") or "unknown", "state": pr.get("state") or "UNKNOWN",
            "draft": pr.get("isDraft"), "mergeable": pr.get("mergeable"),
            "decision": pr.get("reviewDecision"), "passed": passed, "failed": failed,
            "pending": pending, "unresolved": unresolved, "reviews": states, "ready": ready}


def report(number, s):
    print(f"PR #{number} readiness (head {s['head'][:7]}, {s['state']})")
    print(f"CI: {len(s['passed'])} pass, {len(s['failed'])} fail, {len(s['pending'])} pending")
    for name in s["failed"]:
        print(f"  FAIL {name}")
    for name in s["pending"]:
        print(f"  PENDING {name}")
    print(f"Threads: {len(s['unresolved'])} unresolved {s['unresolved']}")
    for state, authors in s["reviews"].items():
        print(f"Reviews {state}: {len(authors)} {authors}")
    print(f"Decision: {s['decision']}")
    print(f"Human approval: {'present' if s['reviews']['APPROVED'] else 'pending (reviewer step)'}")
    print("READY" if s["ready"] else "NOT READY")
    return 0 if s["ready"] else 1


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("usage: python3 pr_readiness.py <pr-number>", file=sys.stderr)
        return 2
    number = int(sys.argv[1])
    return report(number, summary(fetch(number)))


if __name__ == "__main__":
    raise SystemExit(main())
