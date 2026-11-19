"""Guard the PR trigger and cancellation semantics documented in docs/flows/ci-flow.py."""
import os
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CI = Path(os.environ.get("CI_WORKFLOW", ROOT / ".github/workflows/ci.yml"))
TITLE = Path(os.environ.get("PR_TITLE_WORKFLOW", ROOT / ".github/workflows/pr-title.yml"))
BODY = Path(os.environ.get("PR_BODY_WORKFLOW", ROOT / ".github/workflows/pr-body-check.yml"))
LABELER = Path(os.environ.get("LABELER_WORKFLOW", ROOT / ".github/workflows/labeler.yml"))


def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def triggers(workflow):
    # PyYAML follows YAML 1.1 and parses the bare key `on` as boolean True.
    return workflow.get("on", workflow.get(True))


# GitHub defaults a pull_request trigger without an explicit `types` list to
# these activity types, so an absent list means "the default set", not "none".
DEFAULT_PR_TYPES = ["opened", "synchronize", "reopened"]


def event_types(on, name):
    """Activity types GitHub delivers for trigger `name` ([] when it is absent)."""
    if name not in on:
        return []
    event = on[name]
    return list(event["types"]) if isinstance(event, dict) and "types" in event else list(DEFAULT_PR_TYPES)


class TriggerContractTest(unittest.TestCase):
    def test_ci_push_is_main_only(self):
        on = triggers(load(CI))
        self.assertEqual(on["push"]["branches"], ["main"])

    def test_ci_cancels_only_pull_request_runs(self):
        concurrency = load(CI)["concurrency"]
        self.assertIn("github.event.pull_request.number || github.run_id", concurrency["group"])
        self.assertEqual(concurrency["cancel-in-progress"],
                         "${{ github.event_name == 'pull_request' }}")

    def test_rerun_attempt_cannot_cancel_the_current_head_run(self):
        # A rerun of an older pull_request run must land in a different group, or
        # it would cancel the run for the current head and leave its check missing.
        group = load(CI)["concurrency"]["group"]
        self.assertIn("github.run_attempt", group)

    def test_ci_still_runs_on_pr_commits_and_not_on_title_edit(self):
        on = triggers(load(CI))
        types = event_types(on, "pull_request")
        # Assert the trigger still fires for commits; an absent trigger used to
        # return [] here and pass the exclusion check below vacuously.
        self.assertTrue({"opened", "synchronize"}.issubset(set(types)))
        self.assertNotIn("edited", types)

    def test_title_check_runs_on_edit_and_sync(self):
        workflow = load(TITLE)
        on = triggers(workflow)
        self.assertTrue({"edited", "synchronize"}.issubset(set(event_types(on, "pull_request"))))
        self.assertEqual(workflow["permissions"], {"pull-requests": "read"})
        used = [s for s in workflow["jobs"]["validate"]["steps"] if "uses" in s]
        step = next(s for s in used if s["uses"].startswith("amannn/action-semantic-pull-request@"))
        self.assertRegex(step["uses"], r"^amannn/action-semantic-pull-request@[0-9a-f]{40}$")
        allowed = set(step["with"]["types"].split())
        self.assertTrue({"ci", "docs"}.issubset(allowed))

    def test_body_check_runs_on_title_edit(self):
        on = triggers(load(BODY))
        types = event_types(on, "pull_request")
        self.assertTrue({"edited", "opened", "synchronize"}.issubset(set(types)))
        # A paths filter would leave the required check pending on docs-only PRs.
        self.assertNotIn("paths-ignore", on["pull_request"])
        self.assertEqual(load(BODY)["permissions"], {"contents": "read"})

    def test_labeler_does_not_start_on_title_edit(self):
        on = triggers(load(LABELER))
        types = event_types(on, "pull_request_target")
        self.assertTrue({"opened", "synchronize"}.issubset(set(types)))
        self.assertNotIn("edited", types)


if __name__ == "__main__":
    unittest.main()
