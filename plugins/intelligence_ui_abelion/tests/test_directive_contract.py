"""Contract tests for the intelligence-ui-abelion directive.

Run from the repo root:
    python3 -m unittest discover -s plugins/intelligence_ui_abelion/tests -v
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins" / "intelligence_ui_abelion"
CONTRACT = PLUGIN / "docs" / "directive-contract.json"
SOURCE = PLUGIN / "desktop" / "plugin.js"


class DirectiveContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.source = SOURCE.read_text(encoding="utf-8")

    def test_contract_identity(self):
        self.assertEqual(self.contract["version"], 1)
        self.assertEqual(self.contract["directive"], "ui")
        self.assertEqual(self.contract["plugin_id"], "intelligence-ui-abelion")
        self.assertEqual(self.contract["placement"], "alone-on-its-own-line")

    def test_validation_state_and_event_contract(self):
        self.assertEqual(self.contract["common_attrs"], ["version", "id"])
        self.assertEqual(self.contract["validation"]["version"], "1")
        self.assertTrue(self.contract["validation"]["reject_unknown_kind"])
        self.assertEqual(self.contract["state"]["persisted"], ["wizard.done"])
        self.assertTrue(self.contract["events"]["fail_closed"])
        for needle in ("uiStorage.get", "uiStorage.set", "streaming", "Kartu UI tidak didukung"):
            self.assertIn(needle, self.source)

    def test_five_kinds_declared_and_implemented(self):
        expected = {"wizard", "status", "trace", "compare", "form"}
        self.assertEqual(set(self.contract["kinds"]), expected)
        for kind in expected:
            self.assertIn(f"kind === '{kind}'", self.source)

    def test_untrusted_values_and_no_network(self):
        self.assertTrue(self.contract["values_are_untrusted"])
        self.assertFalse(self.contract["secrets_allowed"])
        self.assertFalse(self.contract["network_allowed"])
        self.assertNotIn("fetch(", self.source)
        self.assertNotIn("openExternal", self.source)

    def test_limits_are_bounded(self):
        limits = self.contract["limits"]
        self.assertLessEqual(limits["title_chars"], 120)
        self.assertLessEqual(limits["rows"], 12)
        self.assertLessEqual(limits["prompt_chars"], 500)


if __name__ == "__main__":
    unittest.main()
