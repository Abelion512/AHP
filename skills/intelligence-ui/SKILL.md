---
name: intelligence-ui
description: Use when answers need visual, interactive UI cards.
version: 0.1.0
author: Abelion (@belbelion), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ui, visual, interactive, generative-ui, widget]
    category: creative
    related_skills: [hermes-agent, impeccable, design-md]
---

# Intelligence UI Skill

Hermes has two UI transports. Prefer the NATIVE one: the
`abelion-intelligence-ui` desktop plugin claims `::ui{...}` and renders React
cards inline in Desktop and WebApp. `::preview{file="..."}` is the fallback: a
live but sandboxed HTML iframe. This skill teaches composition; it does not
patch core.

## When to Use

- The person says they are lazy to read, or asks for a visual / interactive
  answer.
- The answer is a wizard, comparison, dashboard, status board, chart, or form.
- Structured output has more than three fields or an ordered procedure.

## Prerequisites

- Desktop app or WebApp with the transcript preview directive enabled (core
  default). CLI and text-only clients show the standard preview card instead.
- A writable workspace path for the single HTML file.
- No extra dependency, credential, or MCP server.

## How to Run

1. First choice — native React, no iframe: emit `::ui{kind="wizard"
   title="Judul" steps="A|B|C"}` alone on its own line. The installed
   `abelion-intelligence-ui` plugin claims the `ui` directive. Kinds: `wizard`,
   `status` (`items="Label:status|..."`), `trace` (`steps="Input|Bukti|Keputusan"`),
   `compare` (`left="A|B" right="C|D" pick="left"`), and
   `form` (`fields="Nama|Catatan" submit="Kirim"`). One card per reply: stacked
   directives are not parsed by v0.23.1.
2. Fallback only — if the plugin is absent, use `write_file` to create one
   self-contained HTML file, then put `::preview{file="/absolute/path/card.html"}`
   alone on its own line. Inline or mid-prose directives stay plain text.
3. Keep the surrounding prose to one to three short lines.

## Quick Reference

| Intent | Shape |
|---|---|
| What should I do | Wizard: 3–6 steps, progress bar, one send button per step |
| A versus B | Two aligned columns, one highlighted recommendation |
| Why | Collapsible `details` with three evidence nodes |
| Numbers | Inline SVG, redrawn on `resize` |
| Status | One row per item, dot plus short label |

## Procedure

1. Pick one dominant shape from the Quick Reference. Do not combine all of them.
2. Write the HTML with `write_file`: inline CSS and JS, no sibling assets.
3. Use only theme tokens: `var(--foreground)`, `var(--muted-foreground)`,
   `var(--accent)`, `var(--border)`, `var(--card)`. The frame injects these, the
   application font, zero body margin, and a transparent background.
4. Lay content flush left. The frame spans the transcript column up to 960px
   and reports height up to 1200px; a centered wrapper wastes that geometry.
5. Wire interaction with `data-hermes-send="short sentence"` on a clickable
   element. Prompts are human-speed and length-capped; never encode a payload,
   command, or secret in them.
6. Keep credentials out of the HTML. The preview is a sandboxed opaque-origin
   document with no access to application storage or privileged bridges.
7. Finish with one text-only line carrying the decision or the single next
   action, so a non-visual client still has the answer.

## Pitfalls

- Writing the directive before the file exists: the card falls back to a plain
  attachment or empty frame.
- Hardcoded colors, fonts, or margins: they break skin and theme changes.
- Duplicating the entire card in chat prose: that defeats the purpose.
- Depending on relative image or script files: opaque-origin documents do not
  resolve sibling assets.
- Install the native plugin by linking its `desktop/` folder into
  `$HERMES_HOME/desktop-plugins/abelion-intelligence-ui`; the loader follows
  linked plugin folders, so do not write plugin files under the guarded home.
- When composing children arrays in `jsx()`, a `forEach` that creates a node
  must `children.push(...)` it. A syntactically valid file can still render an
  empty card; verify the rendered DOM, not just `node --check`.
- Hide counters and progress on rowless cards. A `status` or `form` card has
  no `steps`, so an unconditional `done.length / rows.length` paints `0 / 0`.
- Serving the plugin file is not registration. A 200 from
  `/api/desktop-plugins/read` proves load only; only a rendered `::ui{...}`
  directive proves the directive was claimed in the renderer.
- Claiming a button worked without observing its visible state or delivery ack.

## Verification

- Use `read_file` to confirm the file exists and note its byte count.
- Parse the HTML with a standard-library parser: all five theme tokens present,
  no external `script src`, no `fetch(`, and a `data-hermes-send` attribute for
  every claimed interaction.
- Confirm the native plugin is served: `GET /api/desktop-plugins/list` from
  the WebApp origin must include `abelion-intelligence-ui`. Then send one
  `::ui{...}` reply and read the live DOM: the card's title, rows and buttons
  must be text, never raw directive syntax. A served file alone is not a
  registration check.
- In Desktop or WebApp, confirm the directive renders as a card rather than
  raw text. A text-only client falls back to prose.
- Run `scripts/run_tests.sh tests/skills/test_intelligence_ui_skill.py -q`
  before opening the pull request.
