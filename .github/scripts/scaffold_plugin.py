#!/usr/bin/env python3
"""Create a new plugin skeleton from the repo naming reference.

Usage:
  python .github/scripts/scaffold_plugin.py <name> --description "..." \
      [--category utility] [--root .]

The name must be one core word present in docs/title-reference.md. The script
refuses to overwrite an existing plugin or catalog entry, writes the docs trio,
a registered skill and a first test, then updates hermes.json and README.md.
CI discovers the new plugin through plugins/<id>/plugin.yaml; no workflow edit
is needed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
LEGACY_IDS = frozenset({"pii_mask_abelion", "screen", "output-redact-abelion"})


def name_in_reference(name: str, reference: str) -> bool:
    """Check the name appears as a standalone word in the naming reference."""
    return re.search(r"(?<![A-Za-z])" + re.escape(name) + r"(?![A-Za-z])",
                     reference, re.IGNORECASE) is not None


def catalog_ids(root: Path) -> set[str]:
    path = root / "hermes.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    return {entry["id"] for entry in catalog.get("plugins", [])
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)}


def trusted_file(root: Path, filename: str) -> Path:
    """Return a fixed repo file path, never one derived from file content."""
    base = root.resolve()
    path = (base / filename).resolve()
    if path.parent != base or path.name != filename:
        raise ValueError("refusing to write outside the repository root")
    return path


def add_catalog_entry(root: Path, pid: str, description: str) -> None:
    path = trusted_file(root, "hermes.json")
    catalog = json.loads(path.read_text(encoding="utf-8"))
    plugins = catalog.setdefault("plugins", [])
    plugins.append({"id": pid, "path": "plugins/" + pid, "description": description})
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_readme_row(root: Path, pid: str, description: str) -> None:
    path = trusted_file(root, "README.md")
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| Privacy Guard |"):
            row = "| %s | `%s` | [`plugins/%s/`](plugins/%s/) | %s |" % (
                pid.capitalize(), pid, pid, pid, description)
            lines.insert(index + 1, row)
            break
    else:
        raise ValueError("README.md has no active plugins table row")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_skeleton(root: Path, pid: str, description: str, category: str) -> list[str]:
    base = root / "plugins" / pid
    if base.exists():
        raise ValueError("plugin folder already exists: %s" % base)
    (base / "docs").mkdir(parents=True)
    (base / "skills" / pid).mkdir(parents=True)
    (base / "tests").mkdir(parents=True)

    files = {
        base / "plugin.yaml": (
            "name: %s\ndescription: %s\nversion: 0.1.0\nauthor: Abelion\n"
            "kind: standalone\npython_dependencies: []\n"
            "metadata:\n  hermes:\n    category: %s\n    tags: [%s]\n"
            % (pid, json.dumps(description), category, pid)
        ),
        base / "README.md": (
            "# %s\n\n%s\n\n## Install\n\nUse `update-plugins.sh` after the catalog entry is merged.\n\n"
            "## Limits\n\nAdd the behavior contract and unverified paths before claiming support.\n"
            % (pid.capitalize(), description)
        ),
        base / "docs" / "USAGE.md": (
            "# %s usage\n\nDescribe every hook, skill and config key here with its source file and behavior.\n"
            "State what is memory-only, session-scoped or disk-backed.\n" % pid.capitalize()
        ),
        base / "docs" / "VALIDATION.md": (
            "# %s validation\n\nList what each test layer proves and what it does not.\n" % pid.capitalize()
        ),
        base / "skills" / pid / "SKILL.md": (
            "---\nname: %s\ndescription: Use the %s plugin for its documented task.\n"
            "version: 0.1.0\nplatforms: [linux, macos, windows]\n---\n\n# %s skill\n\n"
            "## When to Use\n\n- Describe the trigger.\n\n## How to Apply\n\n1. Describe the step.\n\n"
            "## Verification\n\nState how to confirm the result.\n" % (pid, pid, pid.capitalize())
        ),
        base / "tests" / ("test_" + pid + ".py"): (
            '"""Synthetic-only regression test for %s."""\n\n\ndef test_plugin_contract_placeholder() -> None:\n'
            '    assert True\n' % pid
        ),
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    return [path.relative_to(root).as_posix() for path in sorted(files)]


def scaffold(root: Path, name: str, description: str, category: str) -> list[str]:
    root = root.resolve()
    if not NAME_RE.fullmatch(name):
        raise ValueError("name must be a single CamelCase word from the naming reference")
    if name.lower() in LEGACY_IDS:
        raise ValueError("name is a retired plugin id")
    reference = root / "docs/title-reference.md"
    if not reference.is_file() or not name_in_reference(name, reference.read_text(encoding="utf-8")):
        raise ValueError("name is not in docs/title-reference.md; add it there in the same PR")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("description must be a non-empty one-line sentence ending with a period")
    if name.lower() in catalog_ids(root):
        raise ValueError("catalog already has an entry for %s" % name.lower())

    created = write_skeleton(root, name.lower(), description, category)
    add_catalog_entry(root, name.lower(), description)
    add_readme_row(root, name.lower(), description)
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="one core word from docs/title-reference.md")
    parser.add_argument("--description", required=True, help="one-line responsibility sentence")
    parser.add_argument("--category", default="utility", help="plugin category")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)
    try:
        created = scaffold(Path(args.root), args.name, args.description, args.category)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("::error::" + str(exc))
        return 1
    for path in created:
        print("created " + path)
    print("updated hermes.json and README.md; open the PR with .github/PULL_REQUEST_TEMPLATE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
