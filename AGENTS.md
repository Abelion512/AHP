# AGENTS.md — Hermes plugins monorepo

This repository is the home for ALL of the owner's Hermes Agent plugins, not for any one of them. The live GitHub name is `Abelion512/Stellarium`; older names (`abelion-hermes-plugins`, `AHP`) redirect to it. The local checkout path `$HOME/.hermes/abelion-hermes-plugins` is intentionally unchanged.

Start here, then open the guide of the plugin you are touching. Do not assume the first plugin you read is the repo's default lens.

## Find your plugin

- `hermes.json` is the catalog of active plugins (`id` and `path`). `plugins/PLUGIN_ID/` holds each one; substitute the catalog id for `PLUGIN_ID` in any command.
- Each plugin owns its `README.md`, `AGENTS.md` (plugin-specific rules, pins, commands), `docs/`, `tests/`, `e2e/`, `skills/` as applicable. Plugin-specific facts (Hermes host pin, config snippets, behavior limits) belong there, never in this file.
- `AGENTS.md` is required for every plugin. The scaffold generates it from `.github/plugin-templates/AGENTS.md`, and the plugin contract rejects a plugin that lacks it.
- `site/pending.json` lists plugins still in review (not yet in the catalog).

## Shared infrastructure (plugin-agnostic)

- `.github/workflows/ci.yml` — per-plugin matrix: syntax, unit tests, dependency audit, gitleaks, plugin contract.
- `.github/workflows/e2e.yml` — pinned-host E2E, grouped by each plugin's `e2e/host.json`.
- `.github/e2e_support/abelion_e2e_support/` — shared Hermes+E2E harness.
- `.github/labeler.yml` + `plugins/PLUGIN_ID/.github/labels.yml` — shared labels by folder, plugin labels per plugin.
- `.github/scripts/` — `plugin_contract.py`, `scaffold_plugin.py`, `e2e_matrix.py`, `build_site.py`.
- `update-plugins.sh` — syncs plugins listed in `hermes.json` into `~/.hermes/plugins/`. Does not migrate profiles; see [docs/PLUGIN_MIGRATION.md](docs/PLUGIN_MIGRATION.md).
- `docs/` — repo-level docs: [PLUGIN_PLATFORM.md](docs/PLUGIN_PLATFORM.md), [CI.md](docs/CI.md), [VERSIONING.md](docs/VERSIONING.md), [SESSION_HISTORY.md](docs/SESSION_HISTORY.md), [PRIORITY_LABELS.md](docs/PRIORITY_LABELS.md), [title-reference.md](docs/title-reference.md).
- `.github/retired-source-recovery.md` — recover retired Shield/tool-context/RSI source from a pinned commit.

## Commands (any plugin)

Replace `PLUGIN_ID` with the plugin's catalog id before running these commands; the angle-bracket form is shell redirection syntax and will fail if copied verbatim.

```bash
P=plugins/PLUGIN_ID
python -m compileall -q "$P"
python -m pytest "$P/tests" -q
```

E2E needs the host pin declared in `$P/e2e/host.json` for plugins with host-dependent behavior; see the plugin's `AGENTS.md` for the exact command. Run only the plugin you changed.

## Conventions (all plugins)

- Each plugin folder name equals its runtime ID. Naming theme is cosmic/Latin; no `-abelion` suffixes, no external model-tier labels.
- Test data is synthetic/local-only; no real credentials anywhere.
- Repository-wide rule: never paste real secrets, cookies, map values, or account identifiers into code, docs, skills, or prompts. Use synthetic fixtures with obvious fake values.
- Do not claim a plugin makes stock Hermes, any laptop, or any provider "safe" or "protected". State the exact pinned commit and tested paths; mark what is not covered.
- Do not weaken or disable a required privacy gate to hide a migration or test failure.
- Every behavior change updates code, the plugin's docs, and its test/E2E in the same commit. A behavior is "Proven" only when its E2E passes.
- Function readiness and design readiness are separate. Passing tests does not show a UI plugin matches its design references; report them separately.
- Always open a GitHub PR for every change, and never merge directly to `main` yourself. Even one-line fixes go through a PR with review and a green CI gate. Direct pushes to the default branch are reserved for admin-only accidents (e.g., dependabot rebases).
- Keep feature policy/UI in the plugin; host enforcement and lifecycle belong in the Hermes core fork. Do not duplicate a security boundary in both. Do not vendor `decolua/9router`.
- Do not edit another plugin's files to make yours pass.

## Adding a plugin

- Follow [docs/PLUGIN_PLATFORM.md](docs/PLUGIN_PLATFORM.md) and [.github/plugin-docs-standard.md](.github/plugin-docs-standard.md); start from `.github/plugin-templates/` (or `python .github/scripts/scaffold_plugin.py`).
- Add `plugins/PLUGIN_ID/` with README, AGENTS.md, docs, tests, skills, a `hermes.json` entry, and `e2e/` only when the plugin has host-dependent behavior (see `.github/plugin-templates/PLUGIN_E2E_STANDARD.md`).

## PR rationale gate

Use `.github/PULL_REQUEST_TEMPLATE.md`, the single canonical template. Explain the function in "What changed", the merge reason and stack order in "Why merge this now", and evidence in "Verification". The PR-body check requires substantive answers, not a green CI claim alone. Indonesian headings remain supported for existing PRs.
