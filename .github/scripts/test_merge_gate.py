"""Synthetic-only tests for the merge gate decision logic."""
import unittest

from merge_gate import EXPECTED_SOURCES, evaluate, is_bot, latest_review_states


def check(name: str, status: str = "completed", conclusion: str = "success", slug: str = "github-actions", run: int = 1) -> dict:
    return {"name": name, "status": status, "conclusion": conclusion,
            "app": {"slug": slug},
            "details_url": "https://github.com/Abelion512/Stellarium/actions/runs/" + str(run) + "/job/2"}


def pr(**changes) -> dict:
    value = {"draft": False, "mergeable": True,
             "user": {"login": "author"}, "head": {"sha": "a" * 40}}
    value.update(changes)
    return value


def workflows_for(checks: list[dict]) -> dict[str, str]:
    mapping = {}
    for index, item in enumerate(checks, 1):
        name = item["name"]
        source = EXPECTED_SOURCES.get(name)
        if source and source[0] == "workflow":
            mapping[str(index)] = source[1][0]
    return mapping


def green_inputs():
    checks = []
    run = 1
    for name, (kind, _value) in EXPECTED_SOURCES.items():
        checks.append(check(name, slug=(_value if kind == "app" else "github-actions"), run=run))
        run += 1
    threads = [{"id": "t1", "isResolved": True, "path": "a.py"}]
    reviews = [
        {"user": {"login": "reviewer", "type": "User"}, "state": "APPROVED",
         "commit_id": "a" * 40, "submitted_at": "2026-01-01T00:00:00Z"},
        {"user": {"login": "author", "type": "User"}, "state": "APPROVED",
         "commit_id": "a" * 40, "submitted_at": "2026-01-01T00:00:01Z"},
        {"user": {"login": "sourcery-ai[bot]", "type": "Bot"}, "state": "APPROVED",
         "commit_id": "a" * 40, "submitted_at": "2026-01-01T00:00:02Z"},
    ]
    return checks, threads, reviews


class MergeGateTest(unittest.TestCase):
    def test_green_when_all_conditions_met(self):
        ok, reasons = evaluate(pr(), *green_inputs(), workflows=workflows_for(green_inputs()[0]))
        self.assertTrue(ok, reasons)
        self.assertEqual(reasons, [])

    def test_failed_pending_and_untrusted_checks_block(self):
        checks, threads, reviews = green_inputs()
        checks[0]["conclusion"] = "failure"
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("Validate PR title" in reason for reason in reasons))
        checks[0] = check("Validate PR title", status="in_progress", conclusion=None)
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("status=in_progress" in reason for reason in reasons))
        checks, threads, reviews = green_inputs()
        checks[0]["details_url"] = "https://github.com/Abelion512/Stellarium/actions/runs/999/job/2"
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("untrusted" in reason for reason in reasons))

    def test_missing_check_blocks(self):
        checks, threads, reviews = green_inputs()
        ok, reasons = evaluate(pr(), checks[1:], threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("missing check" in reason for reason in reasons))

    def test_unresolved_thread_blocks(self):
        checks, threads, reviews = green_inputs()
        threads[0]["isResolved"] = False
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("unresolved review thread" in reason for reason in reasons))

    def test_changes_requested_and_missing_human_approval_block(self):
        checks, threads, _ = green_inputs()
        ok, reasons = evaluate(pr(), checks, threads, [], workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("no human approval" in reason for reason in reasons))
        reviews = [{"user": {"login": "reviewer", "type": "User"}, "state": "CHANGES_REQUESTED",
                    "commit_id": "a" * 40, "submitted_at": "2026-01-01T00:00:00Z"}]
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("changes requested by reviewer" in reason for reason in reasons))

    def test_stale_or_bot_approval_does_not_count(self):
        checks, threads, _ = green_inputs()
        reviews = [
            {"user": {"login": "reviewer", "type": "User"}, "state": "APPROVED",
             "commit_id": "b" * 40, "submitted_at": "2026-01-01"},
            {"user": {"login": "helper[bot]", "type": "Bot"}, "state": "APPROVED",
             "commit_id": "a" * 40, "submitted_at": "2026-01-02"},
        ]
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("no human approval" in reason for reason in reasons))

    def test_latest_review_state_wins(self):
        states = latest_review_states([
            {"user": {"login": "a"}, "state": "CHANGES_REQUESTED", "commit_id": "a" * 40, "submitted_at": "2026-01-01"},
            {"user": {"login": "a"}, "state": "APPROVED", "commit_id": "b" * 40, "submitted_at": "2026-01-02"},
            {"user": {"login": "b"}, "state": "APPROVED", "commit_id": "b" * 40, "submitted_at": "2026-01-01"},
            {"user": {"login": "b"}, "state": "DISMISSED", "commit_id": "b" * 40, "submitted_at": "2026-01-02"},
        ])
        self.assertEqual(states, {"a": ("APPROVED", "b" * 40)})

    def test_bot_detection(self):
        self.assertTrue(is_bot({"type": "Bot", "login": "x"}))
        self.assertTrue(is_bot({"type": "User", "login": "x[bot]"}))
        self.assertFalse(is_bot({"type": "User", "login": "reviewer"}))

    def test_draft_conflict_and_pending_mergeability_block(self):
        checks, threads, reviews = green_inputs()
        ok, reasons = evaluate(pr(draft=True, mergeable=False), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("draft" in reason for reason in reasons))
        self.assertTrue(any("merge conflict" in reason for reason in reasons))
        ok, reasons = evaluate(pr(mergeable=None), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("not computed yet" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
