# Native plugin consolidation

This repository keeps one source of truth for the active plugin set: `hermes.json`.
Each entry points at exactly one folder under `plugins/`, and that folder owns its
manifest, docs, tests, skills, and optional end-to-end suite.

## Current layout

| Area | Owner |
|---|---|
| Catalog and install list | `hermes.json`, `update-plugins.sh` |
| Privacy Guard runtime | `plugins/nebula/` |
| Shared CI and gates | `.github/workflows/`, `.github/scripts/` |
| Generated documentation site | `site/`, built from the catalog |

## Retired sources

Shield, RSI learning, tool-context, Bot Screen (`screen`), and the separate
output-redaction package are retired. Privacy Guard was renamed from
`pii_mask_abelion` to `nebula` during the monorepo refactor. Retired source is kept
only as a rollback archive outside the active install catalog. Do not add retired
plugins back to `hermes.json`; the plugin contract checks catalog/folder/id
consistency, and the consolidated-privacy test explicitly rejects the
`output-redact-abelion` id. Follow `docs/PLUGIN_MIGRATION.md` when moving an existing
profile off a retired plugin.

## Adding a plugin

1. Create `plugins/<id>/` with `plugin.yaml`, `README.md`, `docs/USAGE.md`,
   `tests/test_*.py`, and at least one `skills/*/SKILL.md`.
2. Add a matching `id`, `path`, and non-empty `description` to `hermes.json`.
3. From the repository root, run `python .github/scripts/plugin_contract.py .` and
   `python .github/scripts/build_site.py`, then commit the regenerated site.
   `build_site.py` resolves its root from the current working directory, so running
   it elsewhere writes `site/index.html` in the wrong place.

Renames must update the catalog id, folder name, and manifest name together. The
contract requires all three to match.
