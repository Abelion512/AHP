# AGENTS.md — abelion-intelligence-ui plugin

Plugin-specific rules for Intelligence UI. Root `AGENTS.md` stays plugin-neutral.

## Identity

- Folder, manifest `name`, and `hermes.json` id are all `abelion-intelligence-ui`.
- Renders `::ui{...}` directives as native cards in Hermes Desktop and WebApp.
- The directive must be alone on its own line. Stacked directives are not parsed.

## Commands

```bash
cd "$(git rev-parse --show-toplevel)"
P=plugins/abelion-intelligence-ui
python -m compileall -q "$P/tests"
python -m unittest discover -s "$P/tests"
node --check "$P/desktop/plugin.js"
```

The live WebApp smoke is described in `docs/CORE_COMPARISON.md` and `docs/USAGE.md`; it requires a running
WebApp with CDP and is not a CI gate. There is no per-plugin `e2e/host.json`
because the plugin has no host-dependent required behavior.

## Rules

- Use synthetic-only test data. Never paste real secrets, cookies, map values,
  or account identifiers into code, docs, skills, or prompts.
- Form cards forward entered values through `host.composer.submit`. Do not use
  them to collect secrets; credential-like labels require explicit confirmation.
- Do not claim stock Hermes, a laptop, or a provider is "safe"; report tested
  paths and limits from `docs/USAGE.md`.
- Every behavior change updates code, `docs/USAGE.md` status, and the matching
  test in the same commit.
- Open a PR for every change; never push directly to `main`.

## Local references

- `desktop/plugin.js` — renderer entry point.
- `docs/directive-contract.json` — versioned attribute contract and caps.
- `tests/test_directive_contract.py` — contract regressions.
- `skills/intelligence-ui/SKILL.md` — authoring skill.
