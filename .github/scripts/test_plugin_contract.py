#!/usr/bin/env python3
"""Unit tests for the data-driven plugin contract validator."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from plugin_contract import validate


def write_plugin(root: Path, pid: str = "alpha", *, tests: bool = True, e2e: bool = False,
                 skill_description: str = "Do alpha work.", manifest_name: str | None = None) -> Path:
    plugin = root / "plugins" / pid
    (plugin / "docs").mkdir(parents=True)
    (plugin / "skills" / f"{pid}-skill").mkdir(parents=True)
    (plugin / "tests").mkdir()
    (plugin / "plugin.yaml").write_text(
        f'name: {manifest_name or pid}\ndescription: "Synthetic plugin."\nversion: 0.1.0\n',
        encoding="utf-8",
    )
    (plugin / "README.md").write_text("# Synthetic\n", encoding="utf-8")
    (plugin / "docs" / "USAGE.md").write_text("# Usage\n", encoding="utf-8")
    (plugin / "skills" / f"{pid}-skill" / "SKILL.md").write_text(
        f"---\nname: {pid}-skill\ndescription: {skill_description}\n---\n\n# Skill\n",
        encoding="utf-8",
    )
    if tests:
        (plugin / "tests" / "test_behavior.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    if e2e:
        (plugin / "e2e").mkdir()
        (plugin / "e2e" / "README.md").write_text("# E2E\n", encoding="utf-8")
        (plugin / "e2e" / "test_behavior.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        (plugin / "e2e" / "host.json").write_text(
            json.dumps({"repository": "owner/hermes", "ref": "a" * 40}),
            encoding="utf-8",
        )
    return plugin


def write_catalog(root: Path, entries: list[dict]) -> None:
    (root / "hermes.json").write_text(json.dumps({"plugins": entries}), encoding="utf-8")


class PluginContractTests(unittest.TestCase):
    def test_valid_plugin_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            self.assertEqual(validate(root), [])

    def test_missing_tests_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root, tests=False)
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("tests/test_*.py" in error for error in errors), errors)

    def test_missing_docs_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = write_plugin(root)
            (plugin / "docs" / "USAGE.md").unlink()
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("docs/USAGE.md" in error for error in errors), errors)

    def test_missing_skill_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = write_plugin(root)
            (plugin / "skills" / "alpha-skill" / "SKILL.md").unlink()
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("skills" in error for error in errors), errors)

    def test_invalid_skill_description_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root, skill_description="No closing period")
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("skill description" in error for error in errors), errors)

    def test_missing_catalog_entry_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            write_catalog(root, [])
            errors = validate(root)
            self.assertTrue(any("no catalog entry" in error for error in errors), errors)

    def test_catalog_path_traversal_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            write_catalog(root, [{"id": "alpha", "path": "plugins/../alpha"}])
            errors = validate(root)
            self.assertTrue(any("invalid plugin path" in error for error in errors), errors)

    def test_duplicate_catalog_path_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            write_catalog(root, [
                {"id": "alpha", "path": "plugins/alpha"},
                {"id": "alpha", "path": "plugins/alpha"},
            ])
            errors = validate(root)
            self.assertTrue(any("duplicate plugin path" in error for error in errors), errors)

    def test_manifest_name_must_match_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root, manifest_name="other")
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("must match folder" in error for error in errors), errors)

    def test_e2e_requires_host_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = write_plugin(root, e2e=True)
            (plugin / "e2e" / "host.json").unlink()
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("host.json" in error for error in errors), errors)

    def test_e2e_requires_full_commit_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = write_plugin(root, e2e=True)
            (plugin / "e2e" / "host.json").write_text(
                json.dumps({"repository": "owner/hermes", "ref": "main"}),
                encoding="utf-8",
            )
            write_catalog(root, [{"id": "alpha", "path": "plugins/alpha"}])
            errors = validate(root)
            self.assertTrue(any("full 40-character" in error for error in errors), errors)

    def test_no_plugins_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = validate(Path(directory))
            self.assertTrue(any("no plugins found" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
