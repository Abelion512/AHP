# Intelligence UI — usage

## Install

Symlink the `desktop/` folder into a Hermes profile, then restart the host:

```sh
ln -s "$PWD/plugins/abelion-intelligence-ui/desktop" \
  "$HOME/.hermes/desktop-plugins/abelion-intelligence-ui"
```

The catalog id is `abelion-intelligence-ui`. The desktop-plugin directory name keeps the
hyphenated form because that is the host loader's existing convention.

## Directive

Emit the directive alone on its own line in a reply:

```text
::ui{version="1" id="wiz-01" kind="wizard" title="Rotasi" steps="OpenCode|Hermes|9router"}
```

Supported kinds: `wizard`, `status`, `trace`, `compare`, `form`. Values longer than the
contract limits are rejected; untrusted values are rendered as text, never as markup or URLs.

## Status

| Behavior | Status | Evidence |
|---|---|---|
| Five directive kinds render as cards | Proven | `tests/test_directive_contract.py` |
| Bounded attributes and no network egress | Proven | `tests/test_directive_contract.py` |
| Desktop syntax check | Proven | `node --check desktop/plugin.js` |
| Live WebApp card render | Estimated | `e2e/live_webapp_smoke.py` (needs pinned host) |

See [`directive-contract.json`](directive-contract.json) for the versioned contract and
[`CORE_COMPARISON.md`](CORE_COMPARISON.md) for the live smoke result.
