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

    def test_ghost_authors_empty_commits_and_null_conclusion(self):
        data = pr_readiness.summary({
            "headRefOid": "a" * 40, "state": "OPEN", "isDraft": False,
            "mergeable": "UNKNOWN", "reviewDecision": None,
            "commits": {"nodes": []},
            "reviewThreads": {"nodes": [
                {"isResolved": False, "comments": {"nodes": [{"author": None}]}}
            ]},
            "reviews": {"nodes": [{"author": None, "state": "COMMENTED"}]},
        })
        self.assertFalse(data["ready"])
        self.assertEqual(data["unresolved"], ["unknown"])
        self.assertEqual(data["reviews"]["COMMENTED"], ["unknown"])

    def test_queued_check_without_timestamp_is_pending(self):
        data = pr_readiness.summary(payload(
            [{"name": "ci", "status": "QUEUED", "createdAt": None}], [], []))
        self.assertFalse(data["ready"])
        self.assertEqual(data["pending"], ["ci"])

    def test_completed_check_without_conclusion_is_pending(self):
        data = pr_readiness.summary(payload(
            [{"name": "ci", "status": "COMPLETED", "conclusion": None}], [], []))
        self.assertFalse(data["ready"])
        self.assertEqual(data["passed"], [])
        self.assertEqual(data["pending"], ["ci"])

    def test_no_checks_is_not_ready(self):
        data = pr_readiness.summary(payload([], [], []))
        self.assertFalse(data["ready"])

    def test_stale_conclusion_is_a_failure(self):
        data = pr_readiness.summary(payload(
            [{"name": "ci", "status": "COMPLETED", "conclusion": "STALE"}], [], []))
        self.assertFalse(data["ready"])
        self.assertEqual(data["failed"], ["ci"])

    def test_latest_review_state_wins_per_author(self):
        pr = payload([{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}], [], [])
        pr["reviews"]["nodes"] = [
            {"author": {"login": "reviewer"}, "state": "CHANGES_REQUESTED",
             "submittedAt": "2026-01-01T00:00:00Z"},
            {"author": {"login": "reviewer"}, "state": "APPROVED",
             "submittedAt": "2026-01-02T00:00:00Z"},
        ]
        result = pr_readiness.summary(pr)
        self.assertTrue(result["ready"])
        self.assertEqual(result["reviews"]["CHANGES_REQUESTED"], [])
        self.assertEqual(result["reviews"]["APPROVED"], ["reviewer"])

    def test_draft_pr_is_not_ready(self):
        pr = payload([{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}], [], [])
        pr["isDraft"] = True
        self.assertFalse(pr_readiness.summary(pr)["ready"])


if __name__ == "__main__":
    unittest.main()
