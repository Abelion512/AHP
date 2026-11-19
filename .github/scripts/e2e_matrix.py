#!/usr/bin/env python3
"""Build the real-host E2E matrix from plugins/*/e2e/host.json."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
# A PR can change host.json, so the checked-out host repository is untrusted data.
ALLOWED_OWNERS = frozenset({"Abelion512"})


def registered_plugins(root: Path) -> set[str]:
    catalog_path = root / "hermes.json"
    if not catalog_path.is_file():
        return set()
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{catalog_path}: invalid JSON: {exc}") from exc
    plugins = catalog.get("plugins") if isinstance(catalog, dict) else None
    if not isinstance(plugins, list):
        raise ValueError(f"{catalog_path}: plugins must be a list")
    names = set()
    for entry in plugins:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"{catalog_path}: invalid plugin entry: {entry!r}")
        parts = entry["path"].split("/")
        if len(parts) == 2 and parts[0] == "plugins":
            names.add(parts[1])
    return names


def build_matrix(root: Path) -> list[dict[str, str]]:
    """Group E2E suites by their declared repository and commit."""
    registered = registered_plugins(root)
    groups: dict[tuple[str, str], list[str]] = {}
    for e2e_dir in sorted(root.glob("plugins/*/e2e")):
        if not e2e_dir.is_dir() or e2e_dir.parent.name not in registered:
            continue
        host_path = e2e_dir / "host.json"
        if not host_path.is_file():
            raise ValueError(f"{host_path}: missing pinned host configuration")
        try:
            host = json.loads(host_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"{host_path}: invalid JSON: {exc}") from exc
        if not isinstance(host, dict):
            raise ValueError(f"{host_path}: host configuration must be an object")
        repository = host.get("repository")
        ref = host.get("ref")
        if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
            raise ValueError(f"{host_path}: repository must be owner/name")
        if repository.split("/", 1)[0] not in ALLOWED_OWNERS:
            raise ValueError(f"{host_path}: host repository owner is not allowlisted")
        if not isinstance(ref, str) or not SHA_RE.fullmatch(ref):
            raise ValueError(f"{host_path}: ref must be a full 40-character lowercase commit SHA")
        groups.setdefault((repository, ref), []).append(e2e_dir.relative_to(root).as_posix())

    return [
        {"repository": repository, "ref": ref, "paths": " ".join(paths)}
        for (repository, ref), paths in sorted(groups.items())
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    args = parser.parse_args(argv)
    try:
        matrix = build_matrix(Path(args.root).resolve())
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    print(json.dumps(matrix, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
