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


def event_types(event):
    return event.get("types", []) if isinstance(event, dict) else []


class TriggerContractTest(unittest.TestCase):
    def test_ci_push_is_main_only(self):
        on = triggers(load(CI))
        self.assertEqual(on["push"]["branches"], ["main"])

    def test_ci_cancels_only_pull_request_runs(self):
        concurrency = load(CI)["concurrency"]
        self.assertIn("github.event.pull_request.number || github.run_id", concurrency["group"])
        self.assertEqual(concurrency["cancel-in-progress"],
                         "${{ github.event_name == 'pull_request' }}")

    def test_ci_does_not_start_on_title_edit(self):
        on = triggers(load(CI))
        self.assertNotIn("edited", event_types(on.get("pull_request")))

    def test_title_check_runs_on_edit_and_sync(self):
        workflow = load(TITLE)
        on = triggers(workflow)
        self.assertTrue({"edited", "synchronize"}.issubset(set(event_types(on["pull_request"]))))
        self.assertEqual(workflow["permissions"], {"pull-requests": "read"})
        step = workflow["jobs"]["validate"]["steps"][0]
        self.assertRegex(step["uses"], r"^amannn/action-semantic-pull-request@[0-9a-f]{40}$")
        allowed = set(step["with"]["types"].split())
        self.assertTrue({"ci", "docs"}.issubset(allowed))

    def test_body_check_runs_on_title_edit(self):
        self.assertIn("edited", event_types(triggers(load(BODY))["pull_request"]))
        self.assertEqual(load(BODY)["permissions"], {"contents": "read"})

    def test_labeler_does_not_start_on_title_edit(self):
        on = triggers(load(LABELER))
        self.assertNotIn("edited", event_types(on.get("pull_request_target")))


if __name__ == "__main__":
    unittest.main()
