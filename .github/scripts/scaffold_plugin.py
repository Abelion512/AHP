#!/usr/bin/env python3
"""Create a new plugin skeleton from the repo naming reference.

Usage:
  python .github/scripts/scaffold_plugin.py <name> --description "..." \
      [--category utility]   # run from the repository root

The name must be one core word listed under a tier heading (or Our Plugin) in
docs/title-reference.md. The script refuses to overwrite an existing plugin or
catalog entry, writes the docs trio, a plugin AGENTS.md from the shared
template, a registered skill and a first test, then updates hermes.json and
README.md. CI discovers the new plugin through plugins/<id>/plugin.yaml; no
workflow edit is needed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
SKILL_DESC_RE = re.compile(r"^.{1,60}\.$")
LEGACY_IDS = frozenset({"screen"})
README_ANCHOR = "| Privacy Guard |"


def reference_names(reference: str) -> set[str]:
    """Return allowed names from tier/Our Plugin bullets only, case-sensitive."""
    names: set[str] = set()
    in_tiers = False
    for line in reference.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            in_tiers = heading == "Our Plugin" or heading.startswith("Tier Naming")
        elif line.startswith("### ") and in_tiers:
            pass
        elif in_tiers and line.startswith("- "):
            head = re.split(r"[\u2014\u2013(:;,]", line[2:].strip(), maxsplit=1)[0]
            for token in head.split("/"):
                token = token.strip().strip("*").strip("`").strip()
                if NAME_RE.fullmatch(token):
                    names.add(token)
    return names


def trusted_file(root: Path, filename: str) -> Path:
    """Return a fixed repo file path, never one derived from file content."""
    base = root.resolve()
    path = (base / filename).resolve()
    if path.parent != base or path.name != filename:
        raise ValueError("refusing to write outside the repository root")
    return path


def _load_catalog(root: Path) -> tuple[Path, dict, list]:
    path = trusted_file(root, "hermes.json")
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        raise ValueError("hermes.json must be a JSON object")
    entries = catalog.get("plugins", [])
    if not isinstance(entries, list):
        raise ValueError("hermes.json plugins must be a list")
    return path, catalog, entries


def catalog_ids(root: Path) -> set[str]:
    _, _, entries = _load_catalog(root)
    return {entry["id"] for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)}


def _atomic_write(path: Path, text: str) -> None:
    """Write a fixed trusted file via one replace, then validate its location."""
    target = trusted_file(path.parent, path.name)
    temp = target.with_name(target.name + ".scaffold.tmp")
    with temp.open("w", encoding="utf-8") as handle:
        handle.write(text)
    temp.replace(target)


def add_catalog_entry(root: Path, pid: str, description: str) -> None:
    path, catalog, entries = _load_catalog(root)
    # Preserve existing entries verbatim, including any extra per-plugin fields.
    updated = [item for item in entries if isinstance(item, dict)]
    updated.append({"id": pid, "path": "plugins/" + pid, "description": description})
    catalog["plugins"] = updated
    _atomic_write(path, json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")


def add_readme_row(root: Path, pid: str, description: str) -> None:
    path = trusted_file(root, "README.md")
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(README_ANCHOR):
            row = "| %s | `%s` | [`plugins/%s/`](plugins/%s/) | %s |" % (
                pid.capitalize(), pid, pid, pid, description)
            lines.insert(index + 1, row)
            break
    else:
        raise ValueError("README.md has no active plugins table row")
    _atomic_write(path, "\n".join(lines) + "\n")


def _skill_description(pid: str) -> str:
    description = "Use the %s plugin for its documented task." % pid
    if not SKILL_DESC_RE.fullmatch(description):
        raise ValueError("plugin name is too long for a 60-character skill description")
    return description


def _agents_guide(root: Path, pid: str) -> str:
    """Use the shared template when present; keep scaffolding usable in fixtures."""
    template = root / ".github" / "plugin-templates" / "AGENTS.md"
    if template.is_file():
        return template.read_text(encoding="utf-8").replace("PLUGIN_ID", pid)
    return (
        "# AGENTS.md — %s plugin\n\n"
        "Replace PLUGIN_ID with the catalog id in the shared template. Keep plugin-specific\n"
        "rules, the host pin, and scoped commands in this file.\n\n"
        "## Rules\n\n"
        "- Use synthetic-only test data; never paste real secrets, cookies, map values,\n"
        "  or account identifiers into code, docs, skills, or prompts.\n"
        "- Do not claim stock Hermes, a laptop, or a provider is safe; report exact pins.\n"
        "- Update code, docs/USAGE.md, and tests in the same commit.\n"
        "- Open a PR for every change; never push directly to main.\n" % pid
    )


def write_skeleton(root: Path, pid: str, description: str, category: str,
                   skill_description: str) -> list[str]:
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
            % (json.dumps(pid), json.dumps(description), json.dumps(category), json.dumps(pid))
        ),
        base / "README.md": (
            "# %s\n\n%s\n\n## Install\n\nUse `update-plugins.sh` after the catalog entry is merged.\n\n"
            "## Limits\n\nAdd the behavior contract and unverified paths before claiming support.\n"
            % (pid.capitalize(), description)
        ),
        base / "AGENTS.md": _agents_guide(root, pid),
        base / "docs" / "USAGE.md": (
            "# %s usage\n\nDescribe every hook, skill and config key here with its source file and behavior.\n"
            "State what is memory-only, session-scoped or disk-backed.\n" % pid.capitalize()
        ),
        base / "docs" / "VALIDATION.md": (
            "# %s validation\n\nList what each test layer proves and what it does not.\n" % pid.capitalize()
        ),
        base / "skills" / pid / "SKILL.md": (
            "---\nname: %s\ndescription: %s\n"
            "version: 0.1.0\nplatforms: [linux, macos, windows]\n---\n\n# %s skill\n\n"
            "## When to Use\n\n- Describe the trigger.\n\n## How to Apply\n\n1. Describe the step.\n\n"
            "## Verification\n\nState how to confirm the result.\n"
            % (json.dumps(pid), json.dumps(skill_description), pid.capitalize())
        ),
        base / "__init__.py": (
            '"""Auto-generated skeleton for %s."""\n\nfrom pathlib import Path\n\n\n'
            'def register(ctx):\n'
            '    register_skill = getattr(ctx, "register_skill", None)\n'
            '    if callable(register_skill):\n'
            '        path = Path(__file__).parent / "skills" / %r / "SKILL.md"\n'
            '        register_skill(%r, path, %r)\n'
            % (pid, pid, pid, skill_description)
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
    if not isinstance(category, str) or not category:
        raise ValueError("category must be a non-empty string")
    if (not isinstance(description, str) or not description.strip()
            or "\n" in description or "\r" in description or "|" in description
            or not description.strip().endswith(".")):
        raise ValueError("description must be a one-line sentence ending with a period and no '|'")

    reference = root / "docs/title-reference.md"
    if not reference.is_file() or name not in reference_names(reference.read_text(encoding="utf-8")):
        raise ValueError("name is not a listed tier name in docs/title-reference.md; add it there in the same PR")
    if name.lower() in catalog_ids(root):
        raise ValueError("catalog already has an entry for %s" % name.lower())

    pid = name.lower()
    skill_description = _skill_description(pid)

    catalog_path = trusted_file(root, "hermes.json")
    readme_path = trusted_file(root, "README.md")
    original_catalog = catalog_path.read_text(encoding="utf-8")
    original_readme = readme_path.read_text(encoding="utf-8")
    if not any(line.startswith(README_ANCHOR) for line in original_readme.splitlines()):
        raise ValueError("README.md has no active plugins table row")

    plugin_dir = root / "plugins" / pid
    try:
        created = write_skeleton(root, pid, description, category, skill_description)
        add_catalog_entry(root, pid, description)
        add_readme_row(root, pid, description)
    except Exception:
        shutil.rmtree(plugin_dir, ignore_errors=True)
        _atomic_write(catalog_path, original_catalog)
        _atomic_write(readme_path, original_readme)
        raise
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="one core word from docs/title-reference.md")
    parser.add_argument("--description", required=True, help="one-line responsibility sentence")
    parser.add_argument("--category", default="utility", help="plugin category")
    args = parser.parse_args(argv)
    try:
        created = scaffold(Path.cwd(), args.name, args.description, args.category)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("::error::" + str(exc))
        return 1
    for path in created:
        print("created " + path)
    print("updated hermes.json and README.md; open the PR with .github/PULL_REQUEST_TEMPLATE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
