"""Synthetic-only tests for the plugin scaffold tool."""
import json
import tempfile
import unittest
from pathlib import Path

from scaffold_plugin import name_in_reference, scaffold


def make_root(path: Path) -> Path:
    (path / ".github/scripts").mkdir(parents=True)
    (path / "docs").mkdir(parents=True)
    (path / "README.md").write_text(
        "# Plugins\n\n## Active plugins\n\n| Plugin | Runtime ID | Source | Responsibility |\n"
        "|---|---|---|---|\n"
        "| Privacy Guard | `nebula` | [`plugins/nebula/`](plugins/nebula/) | Masking. |\n",
        encoding="utf-8")
    (path / "hermes.json").write_text(
        json.dumps({"plugins": [{"id": "nebula", "path": "plugins/nebula", "description": "Masking."}]}),
        encoding="utf-8")
    (path / "docs/title-reference.md").write_text(
        "## Stellarium\n- Sol — primary service\n- Luna — cache\n- Proxima — fallback\n",
        encoding="utf-8")
    return path


class ScaffoldTest(unittest.TestCase):
    def test_name_must_be_standalone_word(self):
        self.assertTrue(name_in_reference("Sol", "The Sol service."))
        self.assertFalse(name_in_reference("Sol", "The Solstice service."))

    def test_scaffold_creates_contract_files_and_updates_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            created = scaffold(root, "Proxima", "Fallback companion service.", "utility")
            base = root / "plugins/proxima"
            for rel in ("plugin.yaml", "README.md", "docs/USAGE.md", "docs/VALIDATION.md",
                        "skills/proxima/SKILL.md", "tests/test_proxima.py"):
                self.assertTrue((base / rel).is_file(), rel)
            self.assertIn("plugins/proxima/plugin.yaml", created)
            catalog = json.loads((root / "hermes.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["plugins"][-1]["id"], "proxima")
            self.assertIn("| Proxima | `proxima` |", (root / "README.md").read_text(encoding="utf-8"))

    def test_refuses_unknown_name_existing_plugin_and_bad_description(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            for name, description in (("Vega", "Valid sentence."),
                                      ("Nebula", "Valid sentence."),
                                      ("Luna", "")):
                with self.subTest(name=name, description=description):
                    with self.assertRaises(ValueError):
                        scaffold(root, name, description, "utility")
            self.assertFalse((root / "plugins/luna").exists())


if __name__ == "__main__":
    unittest.main()
