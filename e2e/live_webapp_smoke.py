"""Live WebApp smoke for the abelion-intelligence-ui transcript directive.

Requires a reachable WebApp at http://127.0.0.1:9120 and a Chromium-family
browser with CDP on 127.0.0.1:9222, already logged into the WebApp.

Usage:
    python3 e2e/live_webapp_smoke.py --title "E2E smoke"

Exit 0 only when the card was observed as rendered native text, not raw
directive syntax. No credentials are read or printed.
"""

import argparse
import asyncio
import json
import urllib.request

WEBAPP = "http://127.0.0.1:9120/"
VERSION_URL = "http://127.0.0.1:9222/json/version"


class Cdp:
    # `eval` here sends Runtime.evaluate to our own CDP target; it is not JS
    # eval() of untrusted input. All injected values are JSON/regex escaped.
    def __init__(self, ws, session_id=None):
        self.ws = ws
        self.session_id = session_id
        self.n = 0

    async def send(self, method, params=None):
        self.n += 1
        mid = self.n
        msg = {"id": mid, "method": method, "params": params or {}}
        if self.session_id:
            msg["sessionId"] = self.session_id
        await self.ws.send(json.dumps(msg))
        while True:
            data = json.loads(await self.ws.recv())
            if data.get("id") == mid:
                return data

    async def eval(self, expression):
        result = await self.send(
            "Runtime.evaluate", {"expression": expression, "returnByValue": True}
        )
        return result.get("result", {}).get("result", {}).get("value")


async def wait_until(page: "Cdp", expression: str, deadline: float, label: str) -> bool:
    """Poll a readiness expression until the shared deadline instead of using fixed sleeps."""
    while asyncio.get_event_loop().time() < deadline:
        if await page.eval(expression):
            return True
        await asyncio.sleep(0.5)
    return False


async def smoke(title: str, timeout: float) -> dict:
    try:
        import websockets
    except ModuleNotFoundError as exc:
        return {"ok": False, "reason": "missing dependency: pip install websockets", "error": str(exc)}
    if '"' in title or "\n" in title or "\r" in title:
        return {"ok": False, "reason": "title must not contain quotes or newlines"}
    with urllib.request.urlopen(VERSION_URL, timeout=5) as response:
        endpoint = json.load(response)["webSocketDebuggerUrl"]

    async with websockets.connect(
        endpoint,
        max_size=64 * 1024 * 1024,
        additional_headers={"Origin": "devtools://devtools"},
    ) as ws:
        browser = Cdp(ws)
        created = await browser.send("Target.createTarget", {"url": WEBAPP})
        target_id = created["result"]["targetId"]
        try:
            attached = await browser.send(
                "Target.attachToTarget", {"targetId": target_id, "flatten": True}
            )
            page = Cdp(ws, attached["result"]["sessionId"])
            await page.send("Page.enable")
            await page.send("Runtime.enable")
            await page.send("Page.reload", {"ignoreCache": True})
            deadline = asyncio.get_event_loop().time() + timeout
            if not await wait_until(page, "Boolean(document.querySelector('[role=textbox]'))", deadline, "composer"):
                return {"ok": False, "reason": "composer not found within deadline"}
            await page.eval(
                "(()=>{const b=[...document.querySelectorAll('button,[role=button]')]"
                ".find(x=>(x.innerText||'').trim().startsWith('New session'));"
                "if(b)b.click();return true})()"
            )
            if not await wait_until(page, "Boolean(document.querySelector('[role=textbox]'))", deadline, "fresh session"):
                return {"ok": False, "reason": "fresh session composer not ready"}

            directive = (
                '::ui{version="1" id="e2e-live" kind="status" '
                f'title="{title}" items="Load:ok|Register:ok"' + "}"
            )
            # The directive must stand alone on its own line to be claimed by the renderer.
            await page.send("Input.insertText", {"text": directive})
            await page.send(
                "Input.dispatchKeyEvent",
                {"code": "Enter", "key": "Enter", "type": "keyDown", "windowsVirtualKeyCode": 13},
            )

            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(1)
                observed = await page.eval(
                    "(()=>{const card=document.querySelector('[data-ui-directive=\"status\"]');"
                    "if(!card)return JSON.stringify({card:false});"
                    "const t=card.innerText||'';"
                    "return JSON.stringify({card:true,title:t.includes("
                    + json.dumps(title)
                    + "),load:t.includes('Load'),register:t.includes('Register'),"
                    "raw:(document.body.innerText||'').includes('::ui{')})})()"
                )
                state = json.loads(observed)
                if state.get("card") and state.get("title") and state.get("load") and state.get("register") and not state.get("raw"):
                    return {"ok": True, "title": title, "observed": state}
            tail = await page.eval("(()=>(document.body.innerText||'').slice(-800))()")
            return {"ok": False, "reason": "timeout", "title": title, "tail": tail}
        finally:
            await browser.send("Target.closeTarget", {"targetId": target_id})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="E2E live")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    result = asyncio.run(smoke(args.title, args.timeout))
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
