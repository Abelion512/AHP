#!/usr/bin/env python3
"""Validate every plugin folder against the shared repository contract.

The check is data-driven: it discovers plugins through repository globs and the
catalog. Adding a plugin must not require editing this file or the CI workflow.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DESC_RE = re.compile(r"^.{1,60}\.$")
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SKILL_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
PLUGIN_PATH_RE = re.compile(r"^plugins/([A-Za-z0-9][A-Za-z0-9_-]*)$")


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _check_manifest(plugin_dir: Path, errors: list[str]) -> dict | None:
    pid = plugin_dir.name
    path = plugin_dir / "plugin.yaml"
    try:
        manifest = _read_yaml(path)
    except Exception as exc:
        errors.append(f"{path}: manifest unreadable: {exc}")
        return None
    if not isinstance(manifest, dict):
        errors.append(f"{path}: manifest must be a mapping")
        return None
    name = manifest.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        errors.append(f"{path}: invalid or missing plugin name: {name!r}")
    elif name != pid:
        errors.append(f"{path}: plugin name {name!r} must match folder {pid!r}")
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{path}: missing description")
    return manifest


def _check_docs(plugin_dir: Path, errors: list[str]) -> None:
    for rel in ("README.md", "docs/USAGE.md"):
        path = plugin_dir / rel
        if not path.is_file():
            errors.append(f"{path}: missing required plugin doc")
    skills = sorted((plugin_dir / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append(f"{plugin_dir / 'skills'}: at least one skills/*/SKILL.md is required")
    for path in skills:
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{path}: unreadable skill file: {exc}")
            continue
        match = SKILL_FRONTMATTER_RE.match(raw)
        if not match:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        try:
            frontmatter = yaml.safe_load(match.group(1))
        except Exception as exc:
            errors.append(f"{path}: frontmatter parse error: {exc}")
            continue
        if not isinstance(frontmatter, dict):
            errors.append(f"{path}: frontmatter must be a mapping")
            continue
        if not isinstance(frontmatter.get("name"), str) or not NAME_RE.fullmatch(frontmatter["name"]):
            errors.append(f"{path}: invalid or missing skill name")
        description = frontmatter.get("description")
        if not isinstance(description, str) or not DESC_RE.fullmatch(description):
            errors.append(f"{path}: skill description must be one sentence of at most 60 characters ending with a period")


def _check_tests(plugin_dir: Path, errors: list[str]) -> None:
    tests = sorted((plugin_dir / "tests").glob("test_*.py"))
    if not tests:
        errors.append(f"{plugin_dir / 'tests'}: at least one tests/test_*.py is required")


def _check_e2e(plugin_dir: Path, errors: list[str]) -> None:
    e2e_dir = plugin_dir / "e2e"
    if not e2e_dir.is_dir():
        return
    if not (e2e_dir / "README.md").is_file():
        errors.append(f"{e2e_dir / 'README.md'}: missing E2E contract")
    if not sorted(e2e_dir.glob("test_*.py")):
        errors.append(f"{e2e_dir}: e2e/ exists but has no test_*.py")
    host_path = e2e_dir / "host.json"
    if not host_path.is_file():
        errors.append(f"{host_path}: missing pinned host configuration")
        return
    try:
        host = json.loads(host_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{host_path}: invalid JSON: {exc}")
        return
    if not isinstance(host, dict):
        errors.append(f"{host_path}: host configuration must be an object")
        return
    repository = host.get("repository")
    ref = host.get("ref")
    if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
        errors.append(f"{host_path}: repository must be owner/name")
    if not isinstance(ref, str) or not SHA_RE.fullmatch(ref):
        errors.append(f"{host_path}: ref must be a full 40-character lowercase commit SHA")


def _check_catalog(root: Path, plugin_ids: set[str], errors: list[str]) -> None:
    path = root / "hermes.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: catalog unreadable: {exc}")
        return
    entries = catalog.get("plugins") if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        errors.append(f"{path}: plugins must be a list")
        return
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append(f"{path}: invalid catalog entry: {entry!r}")
            continue
        rel = entry["path"]
        match = PLUGIN_PATH_RE.fullmatch(rel)
        if not match:
            errors.append(f"{path}: invalid plugin path: {rel!r}")
            continue
        pid = match.group(1)
        if pid in seen:
            errors.append(f"{path}: duplicate plugin path: {rel!r}")
            continue
        seen.add(pid)
        if pid not in plugin_ids:
            errors.append(f"{path}: catalog path has no plugin folder: {rel!r}")
        catalog_id = entry.get("id")
        if catalog_id != pid:
            errors.append(f"{path}: catalog id {catalog_id!r} does not match path {rel!r}")
    for pid in sorted(plugin_ids - seen):
        errors.append(f"{path}: plugin {pid!r} has no catalog entry")


def validate(root: Path) -> list[str]:
    """Return every contract violation under ``root`` without short-circuiting."""
    errors: list[str] = []
    plugin_dirs = sorted(path.parent for path in root.glob("plugins/*/plugin.yaml"))
    if not plugin_dirs:
        return [f"{root / 'plugins'}: no plugins found"]
    for plugin_dir in plugin_dirs:
        _check_manifest(plugin_dir, errors)
        _check_docs(plugin_dir, errors)
        _check_tests(plugin_dir, errors)
        _check_e2e(plugin_dir, errors)
    _check_catalog(root, {path.name for path in plugin_dirs}, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    errors = validate(root)
    if errors:
        print("::error::plugin contract violations")
        for error in errors:
            print(f"::error::  {error}")
        return 1
    count = len(list(root.glob("plugins/*/plugin.yaml")))
    print(f"plugin contract OK ({count} plugin(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
