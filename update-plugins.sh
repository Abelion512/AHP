#!/usr/bin/env bash
# update-plugins: sync active monorepo plugin packages to Hermes' plugin directory.
set -euo pipefail

REPO="$HOME/.hermes/abelion-hermes-plugins"
PLUGIN_DIR="$HOME/.hermes/plugins"

if [ ! -d "$REPO/.git" ]; then
  echo "Repo not found at $REPO" >&2
  echo "Clone first: git clone git@github.com:Abelion512/abelion-hermes-plugins.git $REPO" >&2
  exit 1
fi

# A source rename does not uninstall an older copy from a user's Hermes profile.
# Never delete, overwrite, or silently leave a retired plugin discoverable beside
# the consolidated plugin. Require an explicit, backed-up native migration first.
LEGACY_PLUGIN_IDS=(pii_mask_abelion screen output-redact-abelion)
found_legacy=()
for id in "${LEGACY_PLUGIN_IDS[@]}"; do
  if [ -d "$PLUGIN_DIR/$id" ]; then
    found_legacy+=("$id")
  fi
done

if [ "${#found_legacy[@]}" -gt 0 ]; then
  printf 'Legacy Hermes plugin installation detected under %s:\n' "$PLUGIN_DIR" >&2
  printf '  - %s\n' "${found_legacy[@]}" >&2
  cat >&2 <<'MESSAGE'

Update stopped before pulling or syncing anything. This script will not guess
which Hermes profile/config is active and will not edit config or delete plugin
state automatically.

Migration required:
  1. Stop the Hermes gateway/process.
  2. Back up the active Hermes profile configuration and the nebula plus listed
     legacy plugin directories.
  3. Use the installed Hermes version's native plugin management to disable the
     listed legacy plugin IDs. Confirm that only `nebula` owns Privacy Guard.
  4. Move the disabled legacy directories outside ~/.hermes/plugins/ (for
     example, into ~/.hermes/plugin-quarantine/<timestamp>/). Keep them for
     rollback; do not permanently delete them yet.
  5. Re-run this updater, then verify the active plugin list and start a new
     session. Follow docs/PLUGIN_MIGRATION.md for the full procedure.

If native plugin management cannot disable an ID, do not move its directory:
stop and resolve the profile/configuration mismatch first.
MESSAGE
  exit 2
fi

echo "Pulling latest plugins..."
cd "$REPO"
git pull --ff-only

echo "Syncing active plugins to $PLUGIN_DIR..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to read the plugin catalog at $REPO/hermes.json" >&2
  exit 3
fi

# The catalog is the authority for installed plugins. Read it after the pull so
# a newly cataloged plugin is synced without editing this script.
plugin_paths="$(python3 - "$REPO/hermes.json" <<'PY'
import json
import re
import sys
from pathlib import Path

catalog_path = Path(sys.argv[1])
try:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"Invalid plugin catalog {catalog_path}: {exc}")

plugins = catalog.get("plugins") if isinstance(catalog, dict) else None
if not isinstance(plugins, list) or not plugins:
    raise SystemExit(f"Plugin catalog {catalog_path} has no plugins")

seen = set()
for entry in plugins:
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise SystemExit(f"Invalid catalog entry in {catalog_path}: {entry!r}")
    rel = entry["path"]
    parts = rel.split("/")
    if len(parts) != 2 or parts[0] != "plugins" or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", parts[1]):
        raise SystemExit(f"Invalid plugin path in {catalog_path}: {rel!r}")
    if parts[1] in seen:
        raise SystemExit(f"Duplicate plugin path in {catalog_path}: {rel!r}")
    if not (catalog_path.parent / rel / "plugin.yaml").is_file():
        raise SystemExit(f"Catalog plugin has no plugin.yaml: {rel}")
    seen.add(parts[1])
    print(rel)
PY
)" || {
  echo "Failed to read active plugins from $REPO/hermes.json" >&2
  exit 3
}

if [ -z "$plugin_paths" ]; then
  echo "No active plugins found in $REPO/hermes.json" >&2
  exit 3
fi

while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  id="${rel##*/}"
  rsync -a --delete "$REPO/$rel/" "$PLUGIN_DIR/$id/"
  echo "  synced $id"
done <<< "$plugin_paths"

echo
echo "Plugins updated. Restart the gateway and start a new session:"
echo "  hermes gateway restart"
echo "  # or: sudo systemctl restart hermes-gateway"
