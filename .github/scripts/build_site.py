#!/usr/bin/env python3
"""Generate the static site from the plugin catalog and a pending-plugin registry.

Active plugins come from hermes.json. Plugins still in review come from
site/pending.json. Adding a plugin to the catalog is enough to update the site;
no HTML edit is required.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
TITLE = "Abelion Hermes Plugins"
DESCRIPTION = "Standalone Hermes Agent plugins with pinned-host verification and explicit boundaries."
REPO = "https://github.com/Abelion512/Stellarium"


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: unreadable JSON: {exc}") from exc


def active_plugins(root: Path) -> list[dict[str, str]]:
    catalog = read_json(root / "hermes.json")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("plugins"), list):
        raise ValueError("hermes.json must contain a plugins list")
    result = []
    for entry in catalog["plugins"]:
        if not isinstance(entry, dict):
            raise ValueError("catalog entry must be an object")
        pid, path, description = entry.get("id"), entry.get("path"), entry.get("description")
        if not isinstance(pid, str) or not PLUGIN_ID_RE.fullmatch(pid):
            raise ValueError(f"invalid plugin id: {pid!r}")
        if path != "plugins/" + pid:
            raise ValueError(f"catalog path does not match id: {path!r}")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"missing description for {pid}")
        result.append({"id": pid, "description": description.strip(), "status": "active", "url": REPO + "/tree/main/plugins/" + pid})
    return result


def pending_plugins(root: Path) -> list[dict[str, str]]:
    path = root / "site/pending.json"
    if not path.is_file():
        return []
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("plugins"), list):
        raise ValueError("site/pending.json must contain a plugins list")
    result = []
    for entry in data["plugins"]:
        if not isinstance(entry, dict):
            raise ValueError("pending entry must be an object")
        pid, description, url = entry.get("id"), entry.get("description"), entry.get("url")
        if not isinstance(pid, str) or not PLUGIN_ID_RE.fullmatch(pid):
            raise ValueError(f"invalid pending plugin id: {pid!r}")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"missing pending description for {pid}")
        if not isinstance(url, str) or not url.startswith("https://github.com/"):
            raise ValueError(f"invalid pending plugin URL for {pid}")
        result.append({"id": pid, "description": description.strip(), "status": "pending", "url": url})
    return result


def plugin_rows(plugins: list[dict[str, str]]) -> str:
    lines = []
    for number, plugin in enumerate(plugins, 1):
        pid = html.escape(plugin["id"])
        description = html.escape(plugin["description"])
        status = html.escape(plugin["status"])
        url = html.escape(plugin["url"], quote=True)
        lines.append(
            "            <li>\n"
            f'              <span class="seq">{number:02d}</span>\n'
            f'              <a class="pid" href="{url}">{pid}</a>\n'
            f'              <span class="desc">{description}</span>\n'
            f'              <span class="status {status}">{status}</span>\n'
            "            </li>"
        )
    return "\n".join(lines)


def render(root: Path) -> str:
    template = (root / "site/template.html").read_text(encoding="utf-8")
    plugins = active_plugins(root) + pending_plugins(root)
    ids = [plugin["id"] for plugin in plugins]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate plugin id across catalog and pending registry")
    return (template
            .replace("@@TITLE@@", TITLE)
            .replace("@@DESCRIPTION@@", DESCRIPTION)
            .replace("@@PLUGIN_ROWS@@", plugin_rows(plugins)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the generated file differs")
    args = parser.parse_args(argv)
    # Always generate in the current working directory; a CLI-supplied root
    # would let untrusted input choose files outside the repository.
    root = Path.cwd()
    try:
        output = render(root)
    except ValueError as exc:
        print("::error::" + str(exc))
        return 1
    target = root / "site/index.html"
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != output:
            print("site/index.html is stale; run python .github/scripts/build_site.py")
            return 1
        print("site/index.html is current")
        return 0
    target.write_text(output, encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
