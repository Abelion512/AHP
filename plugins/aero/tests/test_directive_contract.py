"""Contract tests for the aero directive.

Run from the repo root:
    python3 -m unittest discover -s plugins/aero/tests -v
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins" / "aero"
CONTRACT = PLUGIN / "docs" / "directive-contract.json"
SOURCE = PLUGIN / "desktop" / "plugin.js"


class DirectiveContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.source = SOURCE.read_text(encoding="utf-8")

    def test_contract_identity(self):
        self.assertEqual(self.contract["version"], 1)
        self.assertEqual(self.contract["directive"], "ui")
        self.assertEqual(self.contract["plugin_id"], "aero")
        self.assertEqual(self.contract["placement"], "alone-on-its-own-line")

    def test_validation_state_and_event_contract(self):
        self.assertEqual(self.contract["common_attrs"], ["version", "id"])
        self.assertEqual(self.contract["validation"]["version"], "1")
        self.assertTrue(self.contract["validation"]["reject_unknown_kind"])
        self.assertEqual(self.contract["state"]["persisted"], ["wizard.done"])
        self.assertTrue(self.contract["events"]["fail_closed"])
        for needle in ("storage?.get", "storage?.set", "streaming", "Kartu UI tidak didukung"):
            self.assertIn(needle, self.source)

    def test_eight_kinds_declared_and_implemented(self):
        expected = {"wizard", "status", "trace", "compare", "form", "choice", "flow", "chart"}
        self.assertEqual(set(self.contract["kinds"]), expected)
        for kind in expected:
            self.assertIn(f"kind === '{kind}'", self.source)

    def test_untrusted_values_and_no_network(self):
        self.assertTrue(self.contract["values_are_untrusted"])
        self.assertFalse(self.contract["secrets_allowed"])
        self.assertFalse(self.contract["network_allowed"])
        self.assertNotIn("fetch(", self.source)
        self.assertNotIn("openExternal", self.source)

    def test_live_smoke_emits_exactly_one_balanced_directive(self):
        import importlib.util
        path = PLUGIN / 'e2e' / 'live_webapp_smoke.py'
        spec = importlib.util.spec_from_file_location('aero_live_smoke', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        directive = module.build_status_directive('Browser smoke')
        self.assertEqual(directive, '::ui{version="1" id="e2e-live" kind="status" title="Browser smoke" items="Load:ok|Register:ok"}')
        self.assertEqual(directive.count('{'), 1)
        self.assertEqual(directive.count('}'), 1)
        for bad in ('', 'x' * 81, 'a"b', 'a}b', 'a\nb'):
            with self.subTest(title=bad), self.assertRaises(ValueError):
                module.build_status_directive(bad)

    def test_limits_are_bounded(self):
        limits = self.contract["limits"]
        self.assertLessEqual(limits["title_chars"], 120)
        self.assertLessEqual(limits["rows"], 12)
        self.assertLessEqual(limits["prompt_chars"], 500)


if __name__ == "__main__":
    unittest.main()
