# Abelion Intelligence UI

Native, interactive Intelligence UI cards rendered **inside the Hermes Desktop
and WebApp transcript**. No iframe, no core patch.

## Name

| Field | Value |
|---|---|
| Runtime / plugin id | `abelion-intelligence-ui` |
| Folder | `plugins/abelion_intelligence_ui` |
| Desktop half | `plugins/abelion_intelligence_ui/desktop/plugin.js` |
| Directive | `::ui{...}` |
| Display name | Abelion Intelligence UI |

## Install

The Hermes desktop-plugin loader follows a linked plugin folder. From this
folder:

```sh
ln -s "$PWD/desktop" "$HOME/.hermes/desktop-plugins/abelion-intelligence-ui"
```

Reload the WebApp or Desktop page. No build step, no dependency.

## Directive

Put the directive **alone on its own line** in an assistant reply. Stacked
directives on consecutive lines are not parsed by this Hermes version (upstream
PR #148562 is still open), so use one card per reply.

| kind | attributes | result |
|---|---|---|
| `wizard` | `title`, `steps="A\|B\|C"` | numbered steps, progress bar, Bantu/Sudah |
| `status` | `title`, `items="Label:state\|..."` | status rows with a state dot |
| `trace` | `title`, `steps="Input\|Bukti\|Keputusan"` | collapsible thinking trace |
| `compare` | `title`, `left="A\|B"`, `right="C\|D"`, `pick="left\|right"` | two aligned columns |
| `form` | `title`, `fields="Nama\|Catatan"`, `submit="Kirim"` | labelled inputs that submit through the composer |

Example:

```text
::ui{kind="wizard" title="Rotasi kredensial" steps="OpenCode|Hermes|9router"}
```

All attributes are untrusted strings: capped, split on `|`, and rendered as
React text children. The card never fetches, never touches credentials, and
`host.composer.submit` fails closed when no composer owns the focused session.

Fallback when the plugin is absent: `::preview{file="..."}` (sandboxed HTML
iframe, not native).

## Tests

```sh
python3 -m unittest discover -s plugins/abelion_intelligence_ui/tests -v
cd plugins/abelion_intelligence_ui/desktop && cp plugin.js plugin.mjs && node --check plugin.mjs
```

Live WebApp evidence is recorded in `docs/DIRECTIVE_CONTRACT.md` and
`docs/CORE_COMPARISON.md`.
