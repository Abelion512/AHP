# Live E2E — abelion-intelligence-ui

`live_webapp_smoke.py` drives the real WebApp at `http://127.0.0.1:9120`
through the browser's CDP endpoint on `127.0.0.1:9222`. It sends one
`::ui{version="1" id="e2e-01" kind="status" ...}` reply and asserts the card appears as native text,
not raw directive syntax.

```sh
python3 e2e/live_webapp_smoke.py --title "E2E live" --timeout 90
```

Exit 0 = rendered card observed. Exit 1 = timeout or no card; the JSON result
includes the last page text tail for diagnosis.

Prerequisites: WebApp running, gateway responsive, browser logged in, CDP port
open, and the `websockets` Python package installed (`python3 -m pip install
websockets==15.0.1`). The harness creates and closes its own browser tab; it
creates a chat session in the WebApp. Titles containing quotes or newlines are
rejected because they would break the directive attribute.

The smoke asserts a native `[data-ui-directive="status"]` card exists and contains
the expected rows. Matching page text alone does not count as a pass, and the
directive is sent on its own line without a prose prefix.

This is a live smoke, not a CI gate. It does not run in the plugin unit suite
and does not fabricate success when the model is unavailable.
