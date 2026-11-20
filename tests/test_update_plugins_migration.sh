#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home"
REPO="$HOME/.hermes/abelion-hermes-plugins"
PLUGIN_DIR="$HOME/.hermes/plugins"
mkdir -p "$REPO/.git" "$REPO/plugins/alpha" "$REPO/plugins/beta" "$PLUGIN_DIR" "$TMP/bin"
export CALL_LOG="$TMP/calls.log"
: > "$CALL_LOG"

cat > "$REPO/hermes.json" <<'JSON'
{
  "plugins": [
    {"id": "alpha", "path": "plugins/alpha"},
    {"id": "beta", "path": "plugins/beta"}
  ]
}
JSON
printf 'name: alpha\n' > "$REPO/plugins/alpha/plugin.yaml"
printf 'name: beta\n' > "$REPO/plugins/beta/plugin.yaml"

cat > "$TMP/bin/git" <<'MOCK'
#!/usr/bin/env bash
printf 'git %s\n' "$*" >> "$CALL_LOG"
MOCK
cat > "$TMP/bin/rsync" <<'MOCK'
#!/usr/bin/env bash
printf 'rsync %s\n' "$*" >> "$CALL_LOG"
args=("$@")
src="${args[${#args[@]}-2]}"
dst="${args[${#args[@]}-1]}"
mkdir -p "$dst"
cp -a "$src" "$dst"
MOCK
chmod +x "$TMP/bin/git" "$TMP/bin/rsync"
export PATH="$TMP/bin:$PATH"

# Each retired plugin ID must block before git pull or rsync can mutate a profile.
for id in pii_mask_abelion screen output-redact-abelion abelion-intelligence-ui; do
  mkdir -p "$PLUGIN_DIR/$id"
  set +e
  output="$(bash "$ROOT/update-plugins.sh" 2>&1)"
  status=$?
  set -e
  if [ "$status" -ne 2 ]; then
    printf 'expected exit 2 for %s, got %s\n%s\n' "$id" "$status" "$output" >&2
    exit 1
  fi
  grep -Fq "$id" <<< "$output"
  if [ -s "$CALL_LOG" ]; then
    echo "updater called git/rsync before blocking on $id" >&2
    cat "$CALL_LOG" >&2
    exit 1
  fi
  rm -rf -- "$PLUGIN_DIR/$id"
done

# A clean profile syncs every catalog plugin, not a hardcoded list.
bash "$ROOT/update-plugins.sh" >/dev/null
grep -Fq 'git pull --ff-only' "$CALL_LOG"
grep -Fq "rsync -a --delete $REPO/plugins/alpha/" "$CALL_LOG"
grep -Fq "rsync -a --delete $REPO/plugins/beta/" "$CALL_LOG"

# An invalid catalog path must fail closed before rsync.
: > "$CALL_LOG"
cat > "$REPO/hermes.json" <<'JSON'
{"plugins": [{"id": "escape", "path": "plugins/../escape"}]}
JSON
set +e
output="$(bash "$ROOT/update-plugins.sh" 2>&1)"
status=$?
set -e
if [ "$status" -ne 3 ]; then
  printf 'expected exit 3 for an invalid catalog path, got %s\n%s\n' "$status" "$output" >&2
  exit 1
fi
if grep -Fq 'rsync ' "$CALL_LOG"; then
  echo "updater called rsync for an invalid catalog path" >&2
  cat "$CALL_LOG" >&2
  exit 1
fi

echo "update-plugins migration and catalog tests passed"
