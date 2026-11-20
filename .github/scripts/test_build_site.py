"""Synthetic-only tests for the static site generator."""
import json
import tempfile
import unittest
from pathlib import Path

from build_site import active_plugins, pending_plugins, render


def make_root(path: Path, catalog: dict, pending: dict | None = None) -> Path:
    (path / "site").mkdir(parents=True)
    (path / "hermes.json").write_text(json.dumps(catalog), encoding="utf-8")
    if pending is not None:
        (path / "site/pending.json").write_text(json.dumps(pending), encoding="utf-8")
    (path / "site/template.html.tpl").write_text(
        "@@TITLE@@|@@DESCRIPTION@@|@@PLUGIN_ROWS@@", encoding="utf-8")
    return path


class BuildSiteTest(unittest.TestCase):
    def test_active_plugins_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory), {"plugins": [
                {"id": "nebula", "path": "plugins/nebula", "description": "Masking."}]})
            self.assertEqual(active_plugins(root)[0]["id"], "nebula")
            (root / "hermes.json").write_text(json.dumps({"plugins": [
                {"id": "nebula", "path": "plugins/other", "description": "Bad."}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match id"):
                active_plugins(root)

    def test_pending_plugins_require_safe_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory), {"plugins": []}, {"plugins": [
                {"id": "aero", "description": "Cards.", "url": "javascript:alert(1)"}]})
            with self.assertRaisesRegex(ValueError, "invalid pending plugin URL"):
                pending_plugins(root)

    def test_render_escapes_and_orders_plugins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory), {"plugins": [
                {"id": "nebula", "path": "plugins/nebula", "description": "Masking <data>."}]},
                {"plugins": [{"id": "aero", "description": "Cards & forms.",
                              "url": "https://github.com/Abelion512/Stellarium/pull/30"}]})
            output = render(root)
            self.assertIn("&lt;data&gt;", output)
            self.assertIn("Cards &amp; forms.", output)
            self.assertLess(output.index(">nebula<"), output.index(">aero<"))

    def test_committed_site_matches_generator(self):
        root = Path(__file__).resolve().parents[2]
        self.assertEqual((root / "site/index.html").read_text(encoding="utf-8"), render(root))


if __name__ == "__main__":
    unittest.main()
