"""Synthetic-only tests for the plugin scaffold tool."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scaffold_plugin
from scaffold_plugin import _skill_description, reference_names, scaffold

REFERENCE = (
    "## Our Plugin\n- **Nebula** (`plugins/nebula/`) — Privacy Guard\n\n"
    "## Tier Naming (our own, not external)\n"
    "### Cosmic & Scale\n- Nebula / Stella — small collectors\n- Nova — fast triggers\n\n"
    "### Light & Time\n- Aurora — background\n- Zenith — real-time\n- Proxima — fallback\n"
    "- Yes — enabled path\n\n"
    "## Visible name vs id\n- Id — technical id\n- The — an article\n"
)


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
    (path / "docs/title-reference.md").write_text(REFERENCE, encoding="utf-8")
    return path


class ScaffoldTest(unittest.TestCase):
    def test_only_tier_bullet_names_are_allowed(self):
        names = reference_names(REFERENCE)
        self.assertIn("Nebula", names)
        self.assertIn("Proxima", names)
        self.assertNotIn("nebula", names)
        self.assertNotIn("Title", names)
        self.assertNotIn("The", names)

    def test_scaffold_creates_contract_files_and_updates_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            created = scaffold(root, "Proxima", "Fallback companion service.", "utility")
            base = root / "plugins/proxima"
            for rel in ("plugin.yaml", "README.md", "docs/USAGE.md", "docs/VALIDATION.md",
                        "skills/proxima/SKILL.md", "__init__.py", "tests/test_proxima.py"):
                self.assertTrue((base / rel).is_file(), rel)
            self.assertIn("plugins/proxima/plugin.yaml", created)
            catalog = json.loads((root / "hermes.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["plugins"][-1]["id"], "proxima")
            self.assertIn("| Proxima | `proxima` |", (root / "README.md").read_text(encoding="utf-8"))
            manifest = (base / "plugin.yaml").read_text(encoding="utf-8")
            self.assertIn('name: "proxima"', manifest)
            self.assertIn('category: "utility"', manifest)
            self.assertIn("register_skill(", (base / "__init__.py").read_text(encoding="utf-8"))

    def test_refuses_unknown_name_existing_plugin_and_bad_description(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            cases = (
                ("Vega", "Valid sentence."),
                ("Nebula", "Valid sentence."),
                ("Luna", ""),
                ("Aurora", "Two lines.\nSecond line."),
                ("Aurora", "Has a | pipe."),
                ("Aurora", "No trailing period"),
            )
            for name, description in cases:
                with self.subTest(name=name, description=description):
                    with self.assertRaises(ValueError):
                        scaffold(root, name, description, "utility")
            self.assertFalse((root / "plugins/luna").exists())
            self.assertFalse((root / "plugins/aurora").exists())

    def test_rejects_malformed_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            for payload in ("[]", "null", '{"plugins": null}'):
                with self.subTest(payload=payload):
                    (root / "hermes.json").write_text(payload, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        scaffold(root, "Proxima", "Valid sentence.", "utility")

    def test_quotes_yaml_significant_name_and_category(self):
        category = "utility\npython_dependencies: [evil]"
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            scaffold(root, "Yes", "Valid sentence.", category)
            manifest = (root / "plugins/yes/plugin.yaml").read_text(encoding="utf-8")
            self.assertIn('name: "yes"', manifest)
            self.assertIn(json.dumps(category), manifest)
            self.assertNotIn("\npython_dependencies: [evil]", manifest)

    def test_rejects_name_too_long_for_skill_description(self):
        with self.assertRaises(ValueError):
            _skill_description("x" * 25)

    def test_missing_readme_anchor_leaves_no_partial_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            readme = root / "README.md"
            readme.write_text("# Plugins\n\nNo table here.\n", encoding="utf-8")
            before = readme.read_text(encoding="utf-8")
            with self.assertRaises(ValueError):
                scaffold(root, "Proxima", "Valid sentence.", "utility")
            self.assertFalse((root / "plugins/proxima").exists())
            self.assertEqual(readme.read_text(encoding="utf-8"), before)

    def test_rolls_back_on_later_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            catalog = (root / "hermes.json").read_text(encoding="utf-8")
            readme = (root / "README.md").read_text(encoding="utf-8")
            with patch.object(scaffold_plugin, "add_readme_row", side_effect=OSError("boom")):
                with self.assertRaises(OSError):
                    scaffold(root, "Proxima", "Valid sentence.", "utility")
            self.assertFalse((root / "plugins/proxima").exists())
            self.assertEqual((root / "hermes.json").read_text(encoding="utf-8"), catalog)
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), readme)


if __name__ == "__main__":
    unittest.main()
