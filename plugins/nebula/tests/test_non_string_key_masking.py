"""Values under non-string mapping keys must not bypass request masking."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
mw = importlib.import_module("nebula.pii_middleware")

CANARY = "SyntheticNonStringKeySecretZ9x7Q5v3"


def test_value_under_integer_key_is_masked():
    request = {"messages": [{"role": "user", "content": "ordinary"}],
               "extra_body": {7: "api_key: " + CANARY}}
    result = mw.pii_middleware(request)
    assert result is not None
    assert CANARY not in str(result["request"])
    assert CANARY in request["extra_body"][7]
