# Abelion Hermes Plugins

A monorepo for standalone Hermes Agent plugins. Each plugin owns its implementation, documentation, unit tests, skills, and feature-specific end-to-end tests. Shared CI and the pinned-core E2E harness live under `.github/`.

[![ci](https://github.com/Abelion512/Stellarium/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/ci.yml)
[![e2e](https://github.com/Abelion512/Stellarium/actions/workflows/e2e.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/e2e.yml)
[![CodeQL](https://github.com/Abelion512/Stellarium/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/codeql.yml)
[![Pylint](https://github.com/Abelion512/Stellarium/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/pylint.yml)
[![Pages](https://github.com/Abelion512/Stellarium/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/pages.yml)

Documentation site: <https://abelion512.github.io/Stellarium/>

## Plugins

[`hermes.json`](hermes.json) is the catalog of active plugins. Each entry names a plugin id and its `plugins/<id>/` folder. Plugins still in review are listed in [`site/pending.json`](site/pending.json).

Each plugin owns its `README.md`, `AGENTS.md`, `docs/`, `tests/`, `e2e/`, and `skills/` as applicable. Plugin behavior, host pins, and validation evidence belong in that plugin's docs. The repository root keeps only shared metadata and entry points such as `hermes.json`, `update-plugins.sh`, this README, and GitHub configuration.

## Plugin vs. core

Feature policy and UI stay in each plugin repository. Host-wide enforcement, authorization, lifecycle, and execution guarantees belong in the Hermes core fork. Do not duplicate the same security boundary in both places.

Each plugin declares its own host requirements and limitations in its docs. A green CI run is evidence only for the pinned host and paths that plugin's suite tests; it does not certify stock Hermes, upstream adoption, or an arbitrary environment.

The standalone `decolua/9router` project owns its router implementation. This repository does not vendor or maintain a duplicate adapter.

## CI and security gates

Every workflow pins third-party actions to full commit SHAs and declares explicit token permissions. The gates are:

| Workflow | What it blocks |
|---|---|
| `ci.yml` | Plugin syntax and mandatory tests, dependency-floor audit, secret scan, and the shared plugin contract. |
| `e2e.yml` | Per-plugin real-host E2E against each plugin's pinned commit. |
| `codeql.yml` | Semantic CodeQL analysis for Actions and Python on PRs, pushes and a weekly schedule. |
| `dependency-review.yml` | A PR that introduces a dependency with a known vulnerability (moderate or higher). |
| `pylint.yml` | Errors and warnings in Python files changed by the PR; legacy debt is not re-litigated. |
| `python-package.yml` | Python syntax errors and the `.github/scripts` test suite. |
| `pr-title.yml`, `pr-body-check.yml` | Conventional PR titles and a substantive rationale/verification body. |
| `stronsium-proof.yml` | Produces bounded proof data from the pinned default-branch producer; it never checks out PR code. |

Details, permission scopes, and the current workflow audit live in [`docs/CI.md`](docs/CI.md).

## Validation

CI runs each plugin's own tests and dependency checks, plus real-host E2E suites grouped by the host pin each plugin declares in `e2e/host.json`. CI checks out the exact commit and verifies the imported source. No real provider or production credentials are used. A green CI run is evidence for its tested commit and paths only.

Keep both test layers for each plugin: fast unit tests for behavior, boundaries, and isolation, and E2E tests against the pinned host that inspect recorded provider requests plus delivered output. Neither layer replaces the other. Per-plugin matrices and evidence live in each plugin's `docs/`.

Model-size or marketing labels are not test counts and not guarantees. CI does not call a live model or send real secrets to a remote endpoint; compatibility claims need a separate configured evaluation with recorded evidence.

## Installation and migration

`update-plugins.sh` syncs every plugin listed in `hermes.json` into `~/.hermes/plugins/`. It stops before pulling or syncing if it detects the retired `pii_mask_abelion`, `screen`, or `output-redact-abelion` directories. It does not guess the active profile, edit Hermes configuration, or delete plugin state. Complete the backed-up native migration and quarantine procedure in [`docs/PLUGIN_MIGRATION.md`](docs/PLUGIN_MIGRATION.md) first. Never delete plugin directories from a live profile, and never disable a plugin's required enforcement merely to hide a migration failure.

Retired source can be recovered from Git history as documented in [`.github/retired-source-recovery.md`](.github/retired-source-recovery.md). An old installed copy is separate state and is not deleted merely because its source was removed from this repository.

## Versioning and releases

`hermes.json` is the repository release version; each `plugins/<id>/plugin.yaml` carries that plugin's own version. Releases are tag-driven: a `vMAJOR.MINOR.PATCH` tag must match `hermes.json`, and the release workflow validates it before creating the GitHub Release. See [`docs/VERSIONING.md`](docs/VERSIONING.md). Merging a PR is not a release and does not install anything.

## Repo tooling and agent skills

Shared repeating-task helpers keep plugin maintenance consistent:

- `.github/task-templates/`: templates for plugin creation, CI/labeler, docs, skills, tests, and review-before-merge.
- `.plugins/`: agent-facing skills for plugin creation, use, debugging/reproduction, and testing.
- `.github/triage-priority.md`: ownership and impact-based priority guidance.

These files are workflow guidance, not runtime behavior. A task template does not replace code review, tests, or evidence for the behavior being claimed.
