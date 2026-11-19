#!/usr/bin/env python3
"""Unit tests for the per-plugin E2E host matrix."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from e2e_matrix import build_matrix


def write_catalog(root: Path, *pids: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    catalog = {"plugins": [{"id": pid, "path": f"plugins/{pid}"} for pid in pids]}
    (root / "hermes.json").write_text(json.dumps(catalog), encoding="utf-8")


def write_e2e(root: Path, pid: str, host: dict | None) -> Path:
    e2e = root / "plugins" / pid / "e2e"
    e2e.mkdir(parents=True)
    (e2e / "test_wire.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    if host is not None:
        (e2e / "host.json").write_text(json.dumps(host), encoding="utf-8")
    return e2e


def host(ref: str = "a" * 40, repository: str = "Abelion512/hermes") -> dict:
    return {"repository": repository, "ref": ref}


class E2EMatrixTests(unittest.TestCase):
    def test_no_e2e_returns_empty_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha")
            (root / "plugins" / "alpha").mkdir(parents=True)
            self.assertEqual(build_matrix(root), [])

    def test_plugins_with_same_host_are_grouped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha", "beta")
            write_e2e(root, "alpha", host())
            write_e2e(root, "beta", host())
            self.assertEqual(build_matrix(root), [
                {"repository": "Abelion512/hermes", "ref": "a" * 40,
                 "paths": "plugins/alpha/e2e plugins/beta/e2e"},
            ])

    def test_different_hosts_create_separate_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha", "beta")
            write_e2e(root, "alpha", host(repository="Abelion512/one"))
            write_e2e(root, "beta", host(ref="b" * 40, repository="Abelion512/two"))
            matrix = build_matrix(root)
            self.assertEqual(len(matrix), 2)
            self.assertEqual({(item["repository"], item["ref"]) for item in matrix},
                             {("Abelion512/one", "a" * 40), ("Abelion512/two", "b" * 40)})

    def test_missing_host_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha")
            write_e2e(root, "alpha", None)
            with self.assertRaisesRegex(ValueError, "missing pinned host"):
                build_matrix(root)

    def test_invalid_repository_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha")
            write_e2e(root, "alpha", host(repository="not-a-repo"))
            with self.assertRaisesRegex(ValueError, "repository must be owner/name"):
                build_matrix(root)

    def test_untrusted_owner_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha")
            write_e2e(root, "alpha", host(repository="attacker/hermes"))
            with self.assertRaisesRegex(ValueError, "owner is not allowlisted"):
                build_matrix(root)

    def test_unregistered_or_file_e2e_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha")
            write_e2e(root, "alpha", host())
            write_e2e(root, "orphan", host(repository="attacker/hermes"))
            (root / "plugins" / "beta").mkdir(parents=True)
            (root / "plugins" / "beta" / "e2e").write_text("not a directory", encoding="utf-8")
            self.assertEqual(build_matrix(root), [
                {"repository": "Abelion512/hermes", "ref": "a" * 40, "paths": "plugins/alpha/e2e"},
            ])

    def test_short_ref_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalog(root, "alpha")
            write_e2e(root, "alpha", host(ref="main"))
            with self.assertRaisesRegex(ValueError, "full 40-character"):
                build_matrix(root)


if __name__ == "__main__":
    unittest.main()
