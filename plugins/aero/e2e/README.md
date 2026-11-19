# Live E2E — aero

`live_webapp_smoke.py` drives the real WebApp at `http://127.0.0.1:9120`
through the browser's CDP endpoint on `127.0.0.1:9222`. It sends one
`::ui{version="1" id="e2e-01" kind="status" ...}` reply and asserts the card appears as native text,
not raw directive syntax.

```sh
python3 plugins/aero/e2e/live_webapp_smoke.py --title "E2E live" --timeout 90
```

Exit 0 = rendered card observed. Exit 1 = timeout or no card; the JSON result
includes the last page text tail for diagnosis.

Prerequisites: WebApp running, gateway responsive, browser logged in, CDP port
open. The harness creates and closes its own browser tab; it creates a chat
session in the WebApp.

This is a live smoke, not a CI gate. It does not run in the plugin unit suite
and does not fabricate success when the model is unavailable.

## Deterministic browser seam (CI)

From `plugins/aero/tests/runtime`, run `npm ci`, `npm test`, install Playwright
Chromium, then `npm run test:browser`. This uses the pinned host parser fixture,
real React DOM and Aero with a fake SDK bridge. It creates no user-host session.
Screenshots/report go to `artifacts/` (or `$AERO_ARTIFACTS`). It is not the live
smoke above and does not prove autonomous live-model skill selection.
