# CI and workflow audit

Every workflow under `.github/workflows/` must:

1. pin each third-party action to a full 40-character commit SHA (no tags or branches);
2. declare explicit `permissions` at workflow or job level;
3. avoid `pull_request_target` unless the workflow never checks out or executes PR code.

`git grep -n "uses:" -- .github/workflows` is the audit command (run from the
checkout you are reviewing, so PR changes are included); every hit resolves to a
commit, not a mutable ref. Compare with `git grep -n "uses:" origin/main --
.github/workflows` when you also want the base-branch baseline.

## Workflow map

| Workflow | Trigger | Token permissions | Notes |
|---|---|---|---|
| `ci.yml` | push `main`, PR, weekly schedule, manual | `contents: read` | Plugin matrix, dependency audit, real-host E2E, gitleaks with pinned checksum, docs/manifest lint. |
| `codeql.yml` | push/PR `main`, weekly schedule | `contents: read`, `security-events: write` | Pinned CodeQL action; no private query packs. |
| `dependency-review.yml` | PR to `main` | `contents: read`, `pull-requests: read` | Reads the PR's changed manifests; no PR comment (`comment-summary-in-pr: never`), so fork PRs work with GitHub's forced read-only token. `fail-on-severity: moderate`. |
| `pylint.yml` | push `main`, PR | `contents: read` | Errors + warnings on Python files changed by the diff; `.pylintrc` disables Ruff-owned style categories and exempts only the uninstalled Hermes host modules (`agent`, `hermes_cli`) from `import-error`. |
| `python-package.yml` | push/PR `main` | `contents: read` | flake8 syntax/undefined-name gate plus `.github/scripts` tests with pinned PyYAML and packaging. |
| `pr-title.yml` | PR | `contents: read` | Conventional title check. |
| `pr-body-check.yml` | PR events | `contents: read` | Advisory rationale gate; PR-controlled code runs with a read-only token and no secrets. |
| `labeler.yml` | `pull_request_target` | job: `contents: read`, `pull-requests: write`, `issues: write` | Reads base-branch labels and changed file names only; never checks out or runs PR code. Write scopes are required to create/sync labels. |
| `stronsium-proof.yml` | `pull_request_target` | `contents: read`, `pull-requests: read` | Runs the pinned default-branch producer through the GitHub API; never checks out PR code. |
| `stronsium-proof-tests.yml` | PR touching `.github/stronsium/**` or the proof workflows | `contents: read` | Offline producer unit tests. |
| `pages.yml` | push `main`, manual | `contents: read`, `pages: write`, `id-token: write` | Publishes `site/` from `main` only; no third-party build. |
| `release.yml` | tag `v*.*.*` | job: `contents: write` | Validates the tag against `hermes.json` and requires the tagged commit to be reachable from `main`, then creates a GitHub Release; a rerun treats an existing release as success. |

## Audit result (2026-11-18)

- **Unpinned actions:** none. `actions/checkout`, `setup-python`, `setup-node`,
  `labeler`, `upload-artifact`, and the CodeQL/pages actions all use 40-hex SHAs.
- **Overly broad token scopes:** no workflow has `write-all`. The only write
  scopes are `labeler` (creating and syncing labels), `pages` (deploying the
  static site), `release` (creating a release), and CodeQL's
  `security-events: write` (uploading results).
- **Privileged triggers:** `labeler` and `stronsium-proof` use
  `pull_request_target`. Neither runs PR code: labeler checks out the base branch
  sparsely, and the proof producer runs only default-branch code.
- **Defense-in-depth gap:** `labeler.yml` does not set
  `persist-credentials: false` on its checkout. The token is read-only for
  contents and no PR code runs, so this is low risk, but setting it matches the
  other workflows.
- **Advisory gates:** `pr-body-check.yml` and `pr-title.yml` run code from the PR
  head under `pull_request`. A PR can weaken its own body/title check. They are
  review aids, not a security boundary.
- **Repository default token policy:** the current `gh` token could not read
  `actions/permissions/workflow` (HTTP 403). Every workflow declares explicit
  permissions, so the default only affects future files. Confirm in repository
  settings that the default is read-only.

## Local equivalents

```bash
python -m compileall -q plugins/nebula
python -m pytest plugins/nebula/tests -q
python .github/scripts/test_dependency_floor_audit.py
python .github/scripts/test_labeler_merge_step.py
python .github/scripts/test_plugin_install_step.py
PYTHONPATH=.github/scripts python -m pytest .github/scripts -q
```

E2E requires the pinned Hermes host; see `AGENTS.md`. A green CI run is evidence
for its tested commit and paths only.
