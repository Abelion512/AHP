"""Synthetic-only tests for the merge gate decision logic."""
import unittest
from unittest.mock import patch

import merge_gate
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

    def test_run_re_accepts_singular_and_plural_job_paths(self):
        for url in ("/actions/runs/123/job/456", "/actions/runs/123/jobs/456"):
            with self.subTest(url=url):
                match = merge_gate.RUN_RE.search(url)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), "123")

    def test_plural_jobs_details_url_is_trusted(self):
        checks, threads, reviews = green_inputs()
        checks[0]["details_url"] = "https://github.com/Abelion512/Stellarium/actions/runs/1/jobs/2"
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(checks))
        self.assertTrue(ok, reasons)

    def test_missing_author_login_blocks(self):
        checks, threads, reviews = green_inputs()
        for user in ({"login": None}, {}, None):
            with self.subTest(user=user):
                ok, reasons = evaluate(pr(user=user), checks, threads, reviews,
                                       workflows=workflows_for(checks))
                self.assertFalse(ok)
                self.assertTrue(any("author" in reason for reason in reasons))

    def test_skipped_review_app_checks_are_allowed(self):
        checks, threads, reviews = green_inputs()
        for name in merge_gate.REVIEW_APP_CHECKS:
            item = next((entry for entry in checks if entry["name"] == name), None)
            if item is None:
                checks.append(check(name, conclusion="skipped", slug="socketdev", run=len(checks) + 1))
            else:
                item["conclusion"] = "skipped"
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(checks))
        self.assertTrue(ok, reasons)

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

    def test_skipped_conclusion_blocks(self):
        checks, threads, reviews = green_inputs()
        checks[0]["conclusion"] = "skipped"
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertFalse(ok)
        self.assertTrue(any("Validate PR title" in reason for reason in reasons))

    def test_latest_attempt_keeps_only_newest_check(self):
        old = check("Validate PR title", conclusion="failure", run=1)
        old["started_at"] = "2026-01-01T00:00:00Z"
        new = check("Validate PR title", conclusion="success", run=2)
        new["started_at"] = "2026-01-02T00:00:00Z"
        seen = merge_gate.latest_checks([old, new])
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["conclusion"], "success")

    def test_successful_rerun_of_failed_check_is_green(self):
        checks, threads, reviews = green_inputs()
        failed = dict(checks[0])
        failed["conclusion"] = "failure"
        failed["started_at"] = "2026-01-01T00:00:00Z"
        success = dict(checks[0])
        success["started_at"] = "2026-01-02T00:00:00Z"
        checks = [failed, success] + checks[1:]
        ok, reasons = evaluate(pr(), checks, threads, reviews, workflows=workflows_for(green_inputs()[0]))
        self.assertTrue(ok, reasons)


class MergeGateApiTest(unittest.TestCase):
    """Synthetic API responses only: no network calls."""

    def test_graphql_errors_raise(self):
        with patch.object(merge_gate, "repo", return_value="o/r"), \
             patch.object(merge_gate, "api_request", return_value={"errors": [{"message": "boom"}]}):
            with self.assertRaises(merge_gate.GateError):
                merge_gate.load_threads(1)

    def test_graphql_missing_repository_raises(self):
        for payload in ({"data": {}}, {"data": {"repository": {"pullRequest": None}}}):
            with patch.object(merge_gate, "repo", return_value="o/r"), \
                 patch.object(merge_gate, "api_request", return_value=payload):
                with self.assertRaises(merge_gate.GateError):
                    merge_gate.load_threads(1)

    def test_publish_updates_existing_check(self):
        with patch.object(merge_gate, "repo_path", side_effect=lambda suffix: suffix), \
             patch.object(merge_gate, "gate_check_ids", return_value=[42]), \
             patch.object(merge_gate, "api_request") as request:
            merge_gate.publish("a" * 40, True, [], "https://example.test")
            method, path = request.call_args.args[:2]
            self.assertEqual(method, "PATCH")
            self.assertIn("42", path)

    def test_publish_creates_when_no_existing_check(self):
        with patch.object(merge_gate, "repo_path", side_effect=lambda suffix: suffix), \
             patch.object(merge_gate, "gate_check_ids", return_value=[]), \
             patch.object(merge_gate, "api_request") as request:
            merge_gate.publish("a" * 40, True, [], "https://example.test")
            self.assertEqual(request.call_args.args[0], "POST")

    def test_blocking_result_posts_when_update_unavailable(self):
        with patch.object(merge_gate, "repo_path", side_effect=lambda suffix: suffix), \
             patch.object(merge_gate, "gate_check_ids", side_effect=merge_gate.GateError("list down")), \
             patch.object(merge_gate, "api_request") as request:
            merge_gate.publish_blocking("a" * 40, "API down")
            self.assertEqual(request.call_args.args[0], "POST")
            self.assertEqual(request.call_args.args[2]["conclusion"], "failure")

    def test_read_failure_publishes_blocking_result(self):
        payload = pr(head={"sha": "a" * 40}, base={"ref": "main"}, state="open")
        with patch.object(merge_gate, "load_pr", return_value=payload), \
             patch.object(merge_gate, "load_checks", side_effect=merge_gate.GateError("API down")), \
             patch.object(merge_gate, "publish_blocking") as blocking:
            with self.assertRaises(merge_gate.GateError):
                merge_gate.run_one(1)
            blocking.assert_called_once()
            self.assertEqual(blocking.call_args.args[0], "a" * 40)
            self.assertIn("evaluation failed", blocking.call_args.args[1])

    def test_non_main_base_is_skipped(self):
        payload = pr(base={"ref": "release/1.0"}, state="open")
        with patch.object(merge_gate, "load_pr", return_value=payload), \
             patch.object(merge_gate, "publish") as published:
            self.assertTrue(merge_gate.run_one(1))
            published.assert_not_called()


if __name__ == "__main__":
    unittest.main()
