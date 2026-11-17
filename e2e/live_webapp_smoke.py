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

import websockets

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


async def smoke(title: str, timeout: float) -> dict:
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
            await asyncio.sleep(4)
            await page.eval(
                "(()=>{const b=[...document.querySelectorAll('button,[role=button]')]"
                ".find(x=>(x.innerText||'').trim().startsWith('New session'));"
                "if(b)b.click();return true})()"
            )
            await asyncio.sleep(2)
            ready = await page.eval(
                "(()=>{const e=document.querySelector('[role=textbox]');"
                "if(!e)return false;e.focus();document.execCommand('selectAll',false,null);"
                "document.execCommand('delete',false,null);return true})()"
            )
            if not ready:
                return {"ok": False, "reason": "composer not found"}

            directive = (
                '::ui{version="1" id="e2e-live" kind="status" '
                f'title="{title}" items="Load:ok|Register:ok"}}'
            )
            await page.send("Input.insertText", {"text": "Balas persis satu baris: " + directive})
            await page.send(
                "Input.dispatchKeyEvent",
                {"code": "Enter", "key": "Enter", "type": "keyDown", "windowsVirtualKeyCode": 13},
            )

            deadline = asyncio.get_event_loop().time() + timeout
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(3)
                observed = await page.eval(
                    "(()=>{const t=document.body.innerText||'';"
                    f"const needle={json.dumps(title)};"
                    "const hits=[...t.matchAll(new RegExp(needle.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&'),'g'))].map(m=>m.index);"
                    "if(hits.length<2)return JSON.stringify({hits:hits.length});"
                    "const seg=t.slice(hits[1]);"
                    "return JSON.stringify({hits:hits.length,load:seg.includes('Load'),"
                    "register:seg.includes('Register'),raw:seg.includes('::ui{')})})()"
                )
                state = json.loads(observed)
                if state.get("hits", 0) >= 2:
                    if state.get("load") and state.get("register") and not state.get("raw"):
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
