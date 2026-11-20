"""Unit tests for the post-PR readiness gate's summary logic."""
import unittest

import pr_readiness


def payload(checks, threads, reviews):
    checks = [{"createdAt": "2026-01-01T00:00:00Z", **check} for check in checks]
    return {
        "headRefOid": "a" * 40,
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "reviewDecision": "REVIEW_REQUIRED",
        "commits": {"nodes": [{"commit": {"statusCheckRollup": {"contexts": {"nodes": checks}}}}]},
        "reviewThreads": {"nodes": [
            {"isResolved": resolved, "comments": {"nodes": [{"author": {"login": author}}]}}
            for resolved, author in threads
        ]},
        "reviews": {"nodes": [
            {"author": {"login": author}, "state": state} for author, state in reviews
        ]},
    }


class SummaryTest(unittest.TestCase):
    def test_green_when_checks_done_and_threads_resolved(self):
        checks = [
            {"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "audit", "status": "COMPLETED", "conclusion": "SKIPPED"},
        ]
        data = pr_readiness.summary(payload(
            checks, [(True, "sourcery-ai")], [("kilo-code-bot", "COMMENTED")]))
        self.assertTrue(data["ready"])
        self.assertEqual(len(data["passed"]), 2)
        self.assertEqual(data["failed"], [])
        self.assertEqual(data["pending"], [])
        self.assertEqual(data["unresolved"], [])
        self.assertEqual(data["reviews"]["APPROVED"], [])

    def test_latest_run_wins_for_repeated_check_name(self):
        checks = [
            {"name": "ci", "status": "COMPLETED", "conclusion": "FAILURE",
             "createdAt": "2026-01-01T00:00:00Z"},
            {"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS",
             "createdAt": "2026-01-02T00:00:00Z"},
        ]
        data = pr_readiness.summary(payload(checks, [], []))
        self.assertTrue(data["ready"])
        self.assertEqual(data["passed"], ["ci"])
        self.assertEqual(data["failed"], [])

    def test_blocked_on_failed_pending_unresolved_and_changes_requested(self):
        checks = [
            {"name": "ci", "status": "COMPLETED", "conclusion": "FAILURE"},
            {"name": "e2e", "status": "IN_PROGRESS", "conclusion": None},
        ]
        data = pr_readiness.summary(payload(
            checks, [(False, "sourcery-ai")], [("reviewer", "CHANGES_REQUESTED")]))
        self.assertFalse(data["ready"])
        self.assertEqual(data["failed"], ["ci"])
        self.assertEqual(data["pending"], ["e2e"])
        self.assertEqual(data["unresolved"], ["sourcery-ai"])
        self.assertEqual(data["reviews"]["CHANGES_REQUESTED"], ["reviewer"])


if __name__ == "__main__":
    unittest.main()
