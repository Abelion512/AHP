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


def build_matrix(root: Path) -> list[dict[str, str]]:
    """Group E2E suites by their declared repository and commit."""
    groups: dict[tuple[str, str], list[str]] = {}
    for e2e_dir in sorted(root.glob("plugins/*/e2e")):
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
