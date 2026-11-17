# Verification scope

## Reproduce

From repository root:

```sh
python3 -m unittest discover -s plugins/aero/tests -v
cd plugins/aero/tests/runtime
npm ci
npm test
npx playwright install --with-deps chromium
npm run test:browser
```

The runtime workflow runs these Node/browser commands with a lockfile and
read-only repository permissions. No provider keys, host credentials, live chat,
PR code execution in a privileged context, or installation changes are needed.

## Observed local results

- Python: 5 contract tests passed.
- React 19 DOM: 7 tests passed, zero skips. Actual component code is compiled by
  esbuild; the SDK bridge is a named fake. Exact form values and full payload are
  asserted after real input events. A 240-character overflow refuses delivery.
- Previous renderer negative control: 1/7 passed, 6/7 failed under the same
  React suite. Repaired renderer: 7/7 passed.
- Chromium: 5 native card kinds rendered from directives through the unchanged
  pinned host parser. Wizard toggle, owner-addressed sends, edited form payload,
  reload persistence, cross-owner isolation, composer refusal, trace expansion
  and 390px no-horizontal-overflow assertions passed.
- Browser screenshots `aero-desktop.png` and `aero-mobile.png` were inspected for
  readable layout, visible rows/controls and no clipping. `browser-report.json`
  records the deterministic smoke result. These are test-harness screenshots,
  not screenshots of an installed user's host.

The SDK fake deliberately reports a different focused chat than the card owner.
The routing test therefore fails an implementation that uses focus instead of
renderer-provided ownership. Missing owner, malformed storage, unsupported
version/kind, streaming, text injection and capped values are negative controls.

## Not established

- The installed host loads/enables both the plugin and its skill.
- A live model autonomously selects the skill from an ordinary user request.
- A real gateway/composer accepts and completes a card action in the owning chat.
- Compatibility with all older hosts, full Desktop/WebApp builds or screenreaders.

The optional `e2e/live_webapp_smoke.py` creates a real chat on a prepared local
host. It is not run in CI and was not run during this repair. It asks for an
explicit directive, so even a pass there would not prove autonomous selection.
No live service, profile or installation was modified. Do not report these
remaining checks as done based on deterministic tests or green CI.
