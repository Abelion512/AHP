"""Contract tests for the abelion-intelligence-ui directive.

Run from the repo root:
    python3 -m unittest discover -s plugins/abelion-intelligence-ui/tests -v
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins" / "abelion-intelligence-ui"
CONTRACT = PLUGIN / "docs" / "directive-contract.json"
SOURCE = PLUGIN / "desktop" / "plugin.js"


class DirectiveContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.source = SOURCE.read_text(encoding="utf-8")

    def test_contract_identity(self):
        self.assertEqual(self.contract["version"], 1)
        self.assertEqual(self.contract["directive"], "ui")
        self.assertEqual(self.contract["plugin_id"], "abelion-intelligence-ui")
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

    def test_wizard_progress_persists_across_remount(self):
        # Storage must be wizard-scoped, session-scoped, and persisted on toggle
        # as stable row indices so duplicate labels survive a reload.
        for needle in (
            "const persistable = kind === 'wizard' && !invalid && !streaming",
            "uiStorage.set(storageKey, next)",
            "const storageKey = `${ID}:${version}:${kind}:${sessionId || 'global'}:${cardId}`",
            "if (persistable) persist(done)",
        ):
            self.assertIn(needle, self.source)
        self.assertNotIn("done.map((i) => rows[i])", self.source)

    def test_runtime_caps_match_contract(self):
        limits = self.contract["limits"]
        self.assertIn(f"const MAX_ROW = {limits['row_chars']}", self.source)
        self.assertIn(f"const MAX_PROMPT = {limits['prompt_chars']}", self.source)
        self.assertIn(f"text(attrs.title, {limits['title_chars']})", self.source)
        self.assertIn(f"maxLength: {limits['field_value_chars']}", self.source)
        self.assertIn("if (full.length > MAX_PROMPT)", self.source)

    def test_each_kind_renders_content(self):
        markers = {
            "wizard": "'✓' : String(index + 1)",
            "status": "dot",
            "compare": "ci === 0 ? 'A' : 'B'",
            "form": "type: sensitive ? 'password' : 'text'",
            "trace": "jsx('details'",
        }
        for kind, marker in markers.items():
            with self.subTest(kind=kind):
                self.assertIn(marker, self.source)
        self.assertIn("'data-ui-directive': kind", self.source)


if __name__ == "__main__":
    unittest.main()
