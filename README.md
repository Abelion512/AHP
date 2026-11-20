# Abelion Hermes Plugins

A monorepo for standalone Hermes Agent plugins. Each plugin owns its implementation, documentation, unit tests, skills, and feature-specific end-to-end tests. Shared CI and the pinned-core E2E harness live under `.github/`.

[![ci](https://github.com/Abelion512/Stellarium/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/ci.yml)
[![e2e](https://github.com/Abelion512/Stellarium/actions/workflows/e2e.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/e2e.yml)
[![CodeQL](https://github.com/Abelion512/Stellarium/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/codeql.yml)
[![Pylint](https://github.com/Abelion512/Stellarium/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/pylint.yml)
[![Pages](https://github.com/Abelion512/Stellarium/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/Abelion512/Stellarium/actions/workflows/pages.yml)

Documentation site: <https://abelion512.github.io/Stellarium/>

## Active plugins

| Plugin | Runtime ID | Source | Responsibility |
|---|---|---|---|
| Privacy Guard | `nebula` | [`plugins/nebula/`](plugins/nebula/) | Session-local PII/credential masking, permitted placeholder restoration, and held output redaction. |
| Intelligence UI | `abelion-intelligence-ui` | [`plugins/abelion_intelligence_ui/`](plugins/abelion_intelligence_ui/) | Native interactive transcript cards (`::ui{...}`) in Desktop and WebApp. |

Each plugin folder contains its own `README.md`, `docs/`, `tests/`, `e2e/`, and `skills/` as applicable. The bundled authoring skill lives at [`skills/intelligence-ui/`](skills/intelligence-ui/); the live WebApp smoke lives at [`e2e/`](e2e/). The repository root retains only shared metadata and entry points such as `hermes.json`, `update-plugins.sh`, this README, and GitHub configuration.

## Plugin vs. core

Feature policy and UI stay in the plugin repository. Host-wide enforcement, authorization, lifecycle, and execution guarantees belong in the Hermes core fork. Do not duplicate the same security boundary in both places.

- **Privacy Guard plugin:** credential/PII/path classification, session-local token mapping, bounded restoration, policy configuration, skills, and regression tests.
- **Hermes core:** provider/tool interception, mandatory fail-closed policy gates, session lifecycle, held-stream semantics, and stable native redaction contracts.

The standalone `decolua/9router` project owns its router implementation. This repository does not vendor or maintain a duplicate adapter.

## Security and compatibility

Mandatory Privacy Guard behavior requires the exact Hermes fork commit `9a85916c87d56c2ca00b02fad8918f93ef1816e9` from [`Abelion512/hermes-4gent`](https://github.com/Abelion512/hermes-4gent). CI checks out that commit for real-host tests. This does not certify stock Hermes, prove upstream adoption, or provide a process-wide network firewall. Detection remains heuristic, and unsupported transports are not universally covered.

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

CI runs each plugin's own tests and dependency checks, plus a real-host E2E suite with a synthetic loopback provider and disposable profiles. Each E2E suite pins its host in `e2e/host.json`; CI groups suites by that pin, checks out the exact commit, and verifies the imported source. No real provider or production credentials are used. A green CI run is evidence for its tested commit and paths only.

### Privacy regression strategy

Keep both test layers. Unit tests exercise classifiers, boundaries, capacity, session isolation, and adversarial mutations quickly; E2E tests exercise the pinned Hermes host and inspect recorded provider requests plus delivered output. E2E does not replace unit coverage, and a green unit run alone is not proof of a secure provider boundary.

The privacy suite includes a deterministic 256-case field-name mutation matrix and fail-closed checks for invisible Unicode in sensitive assignments. CI prints test counts in the run summary and continues to run the full real-host suite against a synthetic loopback provider.

The “2.8T” target is not treated as a count of test cases or as a privacy guarantee. CI does **not** call a live 2.8-trillion-parameter model or send real PII/secrets to a remote endpoint. The current evidence is model-agnostic boundary testing: sensitive canaries must not appear in requests observed at the provider or in final user-visible output. Any live-model compatibility claim requires a separate explicitly configured evaluation and recorded evidence.

## Installation and migration

`update-plugins.sh` syncs every plugin listed in `hermes.json` into `~/.hermes/plugins/`. It stops before pulling or syncing if it detects the retired `pii_mask_abelion`, `screen`, or `output-redact-abelion` directories. It does not guess the active profile, edit Hermes configuration, or delete plugin state. Complete the backed-up native migration and quarantine procedure in [`docs/PLUGIN_MIGRATION.md`](docs/PLUGIN_MIGRATION.md) first. Never delete plugin directories from a live profile, and never disable required Privacy Guard merely to hide a migration failure.

Retired source can be recovered from Git history as documented in [`.github/retired-source-recovery.md`](.github/retired-source-recovery.md). An old installed copy is separate state and is not deleted merely because its source was removed from this repository.

## Versioning and releases

`hermes.json` is the repository release version; each `plugins/<id>/plugin.yaml` carries that plugin's own version. Releases are tag-driven: a `vMAJOR.MINOR.PATCH` tag must match `hermes.json`, and the release workflow validates it before creating the GitHub Release. See [`docs/VERSIONING.md`](docs/VERSIONING.md). Merging a PR is not a release and does not install anything.

## Repo tooling and agent skills

Shared repeating-task helpers keep plugin maintenance consistent:

- `.github/task-templates/`: templates for plugin creation, CI/labeler, docs, skills, tests, and review-before-merge.
- `.plugins/`: agent-facing skills for plugin creation, use, debugging/reproduction, and testing.
- `.github/triage-priority.md`: ownership and impact-based priority guidance.

These files are workflow guidance, not runtime behavior. A task template does not replace code review, tests, or evidence for the behavior being claimed.
