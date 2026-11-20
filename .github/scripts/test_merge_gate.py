"""Synthetic-only tests for the merge gate decision logic."""
import unittest

from merge_gate import EXPECTED_CHECKS, evaluate, latest_review_states


def check(name: str, status: str = "completed", conclusion: str = "success") -> dict:
    return {"name": name, "status": status, "conclusion": conclusion}


def pr(**changes) -> dict:
    value = {"draft": False, "mergeable": True, "user": {"login": "author"}}
    value.update(changes)
    return value


def green_inputs():
    checks = [check(name) for name in EXPECTED_CHECKS]
    threads = [{"id": "t1", "isResolved": True, "path": "a.py"}]
    reviews = [
        {"user": {"login": "reviewer"}, "state": "APPROVED", "submitted_at": "2026-01-01T00:00:00Z"},
        {"user": {"login": "author"}, "state": "APPROVED", "submitted_at": "2026-01-01T00:00:01Z"},
        {"user": {"login": "sourcery-ai[bot]"}, "state": "APPROVED", "submitted_at": "2026-01-01T00:00:02Z"},
    ]
    return checks, threads, reviews


class MergeGateTest(unittest.TestCase):
    def test_green_when_all_conditions_met(self):
        ok, reasons = evaluate(pr(), *green_inputs())
        self.assertTrue(ok, reasons)
        self.assertEqual(reasons, [])

    def test_failed_or_pending_check_blocks(self):
        checks, threads, reviews = green_inputs()
        checks[0]["conclusion"] = "failure"
        ok, reasons = evaluate(pr(), checks, threads, reviews)
        self.assertFalse(ok)
        self.assertTrue(any("Validate PR title" in reason for reason in reasons))
        checks[0] = check("Validate PR title", status="in_progress", conclusion=None)
        ok, reasons = evaluate(pr(), checks, threads, reviews)
        self.assertFalse(ok)
        self.assertTrue(any("status=in_progress" in reason for reason in reasons))

    def test_missing_check_blocks(self):
        checks, threads, reviews = green_inputs()
        ok, reasons = evaluate(pr(), checks[1:], threads, reviews)
        self.assertFalse(ok)
        self.assertTrue(any("missing check" in reason for reason in reasons))

    def test_unresolved_thread_blocks(self):
        checks, threads, reviews = green_inputs()
        threads[0]["isResolved"] = False
        ok, reasons = evaluate(pr(), checks, threads, reviews)
        self.assertFalse(ok)
        self.assertTrue(any("unresolved review thread" in reason for reason in reasons))

    def test_changes_requested_and_missing_human_approval_block(self):
        checks, threads, _ = green_inputs()
        ok, reasons = evaluate(pr(), checks, threads, [])
        self.assertFalse(ok)
        self.assertTrue(any("no human approval" in reason for reason in reasons))
        reviews = [{"user": {"login": "reviewer"}, "state": "CHANGES_REQUESTED",
                    "submitted_at": "2026-01-01T00:00:00Z"}]
        ok, reasons = evaluate(pr(), checks, threads, reviews)
        self.assertFalse(ok)
        self.assertTrue(any("changes requested by reviewer" in reason for reason in reasons))

    def test_latest_review_state_wins(self):
        states = latest_review_states([
            {"user": {"login": "a"}, "state": "CHANGES_REQUESTED", "submitted_at": "2026-01-01"},
            {"user": {"login": "a"}, "state": "APPROVED", "submitted_at": "2026-01-02"},
            {"user": {"login": "b"}, "state": "APPROVED", "submitted_at": "2026-01-01"},
            {"user": {"login": "b"}, "state": "DISMISSED", "submitted_at": "2026-01-02"},
        ])
        self.assertEqual(states, {"a": "APPROVED"})

    def test_draft_and_conflict_block(self):
        checks, threads, reviews = green_inputs()
        ok, reasons = evaluate(pr(draft=True, mergeable=False), checks, threads, reviews)
        self.assertFalse(ok)
        self.assertTrue(any("draft" in reason for reason in reasons))
        self.assertTrue(any("merge conflict" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
