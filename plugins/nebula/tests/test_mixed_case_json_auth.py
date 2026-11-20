"""Mixed-case auth field names inside JSON text must still mask their value."""
import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
Guard = importlib.import_module("nebula.guard").Guard

CANARY = "SyntheticMixedCaseAuthZ9x7Q5v3"


@pytest.mark.parametrize("name", [
    "AuThOrIzAtIoN", "Proxy-Authorization", "PRoXy_AuTh", "hF_ToKeN",
])
def test_mixed_case_auth_json_value_is_masked(name):
    inner = json.dumps({"name": name, "value": "Bearer " + CANARY,
                        "note": "ordinary text"})
    text = json.dumps({"payload": inner})
    guard = Guard()
    session = guard.session("mixed-json-auth")
    masked = guard.text(text, session)
    assert CANARY not in masked
    assert "ordinary text" in masked
    assert session.entries
    assert all(entry.kind == "SECRET" for entry in session.entries.values())
    guard.close("mixed-json-auth")


def test_mixed_case_auth_json_is_masked_in_required_request_policy():
    inner = json.dumps({"name": "AuThOrIzAtIoN", "value": CANARY})
    text = json.dumps({"payload": inner})
    before = {"model": "m", "messages": [{"role": "user", "content": text}]}
    result = Guard().required_policy("request", request=before,
                                     session_id="mixed-json-policy")
    assert result["allow"] is True
    assert CANARY not in json.dumps(result["request"])
    assert before["messages"][0]["content"] == text
