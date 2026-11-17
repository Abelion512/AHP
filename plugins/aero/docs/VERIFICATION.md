# Verification scope

## Reproduce deterministic tests

From repository root:

```sh
python3 -m unittest discover -s plugins/aero/tests -v
cd plugins/aero/tests/runtime
npm ci
npm test
npx playwright install --with-deps chromium
npm run test:browser
```

The runtime workflow uses locked dependencies and read-only repository permissions.
No provider keys, host credentials, live chat or installation changes are needed.

## Deterministic results

- Python: 6 contract/serialization tests passed, including exact balanced directive
  output and invalid-title refusal controls.
- React 19 DOM: 7 tests passed, zero skips. Actual component code is compiled by
  esbuild; the SDK bridge is a named fake. Exact edited form values and the full
  submitted payload are asserted after real input events. A 240-character
  overflow refuses delivery.
- Previous renderer negative control: 1/7 passed, 6/7 failed under the same suite.
  Repaired renderer: 7/7 passed.
- Chromium: all 5 kinds rendered through the unchanged byte-pinned host parser.
  Wizard toggles, owner-addressed sends, edited form payload, reload persistence,
  cross-owner isolation, composer refusal, trace expansion and 390px
  no-horizontal-overflow assertions passed.
- `aero-desktop.png` and `aero-mobile.png` were visually inspected for readable
  controls and no clipping. `browser-report.json` records the deterministic
  smoke. These images are test-harness renders, not the installed live host.

The fake SDK reports a focused chat different from the card owner. Missing owner,
malformed storage, unsupported version/kind, streaming, text injection and capped
values are negative controls. This tests behavior, not model selection.

## Authorized temporary live smoke

On 2026-11-18 at 06:38-06:40 Asia/Jakarta, renderer and skill from functional head
`829eeb83332402f1d4f97a83b1e7a3fe4269e989` were tested on the intended Hermes
v0.23.2 host. The owner approved a temporary update followed by exact restoration.
The existing renderer was replaced in place, not installed alongside a second
claimant. Both original files were backed up before replacement.

- An ordinary Indonesian request asked for a short interactive pre-merge
  checklist. It supplied no directive syntax and prohibited file/command work.
- The existing Nous Portal `tencent/hy4-flash:free` model loaded Aero and produced
  a native three-step wizard.
- A local completion toggle visibly changed `0 / 3` to `1 / 3`.
- The help button submitted `Bantu: Cek PR sebelum merge - Baca perubahan` into
  the same owning chat. The real model acknowledged step 1 and stayed in UI-test
  mode without running git or reading files.
- After testing, both originals were restored and SHA256-checked against the
  pre-test manifest. A full page reload and independent served-renderer read
  confirmed the original renderer was active again.

No permanent installation, paid model switch, merge or host restart occurred.
Live screenshots were inspected and delivered privately to the owner; they are
not published here because they contain unrelated workspace/UI context.

## Limits and open findings

- This is one real provider/session smoke, not a promise that every model will
  always select the skill or emit valid cards.
- Live reload persistence was not independently checked with a full reload while
  the repaired renderer was installed. That claim is limited to the deterministic
  Chromium test. Live cross-owner routing was not exercised by switching chats;
  the real action stayed in its owning chat, while cross-owner refusal/isolation
  has deterministic coverage.
- Full Desktop/WebApp builds, all older hosts and screenreader compatibility were
  not established.
- Sonar quality gate passed at the tested functional head, but one open
  `typescript:S2310` code-smell finding remains at line 149 of the byte-pinned
  upstream parser fixture. The assignment advances the parser scan and matches
  the pinned upstream bytes. The fixture is not silently edited to clear a badge.
  A passing gate is not a zero-issue claim.
- An unrelated Gemini side pane already had a React render error before this
  smoke. Aero testing does not fix or validate that plugin.

The optional `e2e/live_webapp_smoke.py` requests an explicit directive and is not
run in CI. The ordinary-request smoke described above was a separate manual
live-host check, not a claim that this optional script was run.
