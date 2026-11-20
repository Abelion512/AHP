# AGENTS.md — PLUGIN_ID plugin

Replace `PLUGIN_ID` with the plugin's catalog id everywhere in this file. Keep this
file in the plugin folder; root `AGENTS.md` stays plugin-neutral.

## Identity

- Folder, manifest `name`, and `hermes.json` id must all be `PLUGIN_ID`.
- State what the plugin does, what it does not do, and which host commit it was
  verified against (in `e2e/host.json` when E2E applies).

## Commands

```bash
cd "$(git rev-parse --show-toplevel)"
P=plugins/PLUGIN_ID
python -m compileall -q "$P"
python -m pytest "$P/tests" -q
```

For host-dependent behavior, describe the pinned E2E command here and keep the
pin in `e2e/host.json`. Do not run full E2E unless needed.

## Rules

- Test data is synthetic and local-only. Never paste real secrets, cookies, map
  values, or account identifiers into code, docs, skills, or prompts.
- Do not claim the plugin makes stock Hermes, a laptop, or a provider "safe".
  Report the exact verified commit, tested paths, and known gaps.
- Every behavior change updates code, `docs/USAGE.md` status, and the matching
  test or E2E in the same commit.
- Do not change another plugin's files to make this one pass.
- Open a PR for every change; never push directly to `main`.

## Local references

- `README.md` — install and limitation summary.
- `docs/USAGE.md` — contract, config keys, and proven/not-proven status.
- `docs/VALIDATION.md` — what each test layer proves and what it does not.
- `tests/` — synthetic-only regressions.
- `skills/` — registered skills with YAML frontmatter.
