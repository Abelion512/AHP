# Workflow hardening, opt-in auto-fix, and skills-driven Pages — design

Date: 2026-11-19
Repo: Abelion512/AHP (`abelion-hermes-plugins`)
Status: approved, implementation in one feature branch with three commits

## Intent

Stop the repeated manual loop of "agent fixes PR comments → user re-prompts → CI fails again".
Make gates authoritative, add an opt-in auto-fix lane, and rebuild the Pages site using the
Hermes skills already installed under `~/.hermes/skills/`. The human still merges; no
auto-merge is in scope.

## Small — gate hardening (no new secret)

- `check_pr_body.py`: enforce all eight sections of `PULL_REQUEST_TEMPLATE.md`. Today only
  `What changed`, `Why merge this now` and `Verification` are enforced.
- `test_pr_body_check.py`: derive the expected missing count from `len(SECTIONS)` so future
  template changes cannot silently weaken the gate.
- New `check_nonempty_pr.py` + workflow step: fail a PR whose `changed_files` is zero. An empty
  PR cannot produce a stronsium proof and previously raised `malformed_producer_source`.

## Big — opt-in auto-fix lane (R2/R3, disabled by default)

- Workflow `auto-fix.yml` guarded by `vars.AUTOFIX_ENABLED == 'true'` and manual
  `workflow_dispatch` with a PR number.
- Eligibility in a pure, unit-tested Python helper: PR open, not draft, same repository,
  `changed_files > 0`.
- Agent runs only from a pinned Hermes commit and a sanitized task file built from review
  comments. PR text is untrusted; no PR code is executed in the privileged job.
- Token: `contents: write`, `pull-requests: write`, scoped to the PR head branch. Requires a
  repository secret for model auth. Shipping the workflow disabled does not add a credential.
- Enabling it needs explicit human approval in this repo.

## Pages — built with Hermes skills

- Redesign `site/index.html` following `~/.hermes/skills/frontend-design`,
  `frontend-ui-engineering` and `design-html`: deliberate type scale, content-grounded visual
  identity, accessible contrast, responsive layout, no AI-template tells.
- Static HTML/CSS only. No dependency, no telemetry, no external assets. `pages.yml` unchanged.

## Delivery

One branch from `main`, three sequential commits (small, big, Pages), one PR. Each commit is
verified locally before the next. Merge only after all checks pass.
