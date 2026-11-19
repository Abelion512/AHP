#!/usr/bin/env python3
"""Unit tests for the per-plugin E2E host matrix."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from e2e_matrix import build_matrix


def write_e2e(root: Path, pid: str, host: dict | None) -> Path:
    e2e = root / "plugins" / pid / "e2e"
    e2e.mkdir(parents=True)
    (e2e / "test_wire.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    if host is not None:
        (e2e / "host.json").write_text(json.dumps(host), encoding="utf-8")
    return e2e


class E2EMatrixTests(unittest.TestCase):
    def test_no_e2e_returns_empty_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plugins" / "alpha").mkdir(parents=True)
            (root / "plugins" / "alpha" / "plugin.yaml").write_text("name: alpha\n", encoding="utf-8")
            self.assertEqual(build_matrix(root), [])

    def test_plugins_with_same_host_are_grouped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = {"repository": "owner/hermes", "ref": "a" * 40}
            write_e2e(root, "alpha", host)
            write_e2e(root, "beta", host)
            self.assertEqual(build_matrix(root), [
                {"repository": "owner/hermes", "ref": "a" * 40,
                 "paths": "plugins/alpha/e2e plugins/beta/e2e"},
            ])

    def test_different_hosts_create_separate_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_e2e(root, "alpha", {"repository": "owner/one", "ref": "a" * 40})
            write_e2e(root, "beta", {"repository": "owner/two", "ref": "b" * 40})
            matrix = build_matrix(root)
            self.assertEqual(len(matrix), 2)
            self.assertEqual({(item["repository"], item["ref"]) for item in matrix},
                             {("owner/one", "a" * 40), ("owner/two", "b" * 40)})

    def test_missing_host_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_e2e(root, "alpha", None)
            with self.assertRaisesRegex(ValueError, "missing pinned host"):
                build_matrix(root)

    def test_invalid_repository_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_e2e(root, "alpha", {"repository": "not-a-repo", "ref": "a" * 40})
            with self.assertRaisesRegex(ValueError, "repository must be owner/name"):
                build_matrix(root)

    def test_short_ref_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_e2e(root, "alpha", {"repository": "owner/hermes", "ref": "main"})
            with self.assertRaisesRegex(ValueError, "full 40-character"):
                build_matrix(root)


if __name__ == "__main__":
    unittest.main()
