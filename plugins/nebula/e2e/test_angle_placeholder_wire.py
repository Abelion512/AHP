"""Real-host angle-prefix regression and benign-reference controls.

Uses the same synthetic loopback provider and pinned-host requirement as the
existing Privacy Guard wire suite. No external model service is contacted.
"""
import pytest
from abelion_e2e_support.host import wire_text, requires_hermes
from test_privacy_wire import chat, REQUIRED_CONFIG

pytestmark = requires_hermes

SAMPLE = "SyntheticAngleWireCanary7M2"
PROMPT = 'api_key="<' + SAMPLE + '"\nDocumentation: api_key="<your-api-key>"\nSay hi.'


def test_unprotected_control_exposes_angle_prefixed_value(tmp_path):
    server = chat(tmp_path, PROMPT, plugins=())
    assert server.main_requests(), "probe did not observe a main request"
    assert SAMPLE in wire_text(server.main_requests()[0])


@pytest.mark.parametrize("required", [False, True], ids=["optional-main", "required-all"])
def test_angle_prefixed_credential_is_masked_at_provider(tmp_path, required):
    server = chat(tmp_path, PROMPT, extra_config=REQUIRED_CONFIG if required else "")
    assert server.main_requests(), "no main request reached the loopback provider"
    observed = server.requests if required else server.main_requests()
    assert observed
    assert all(SAMPLE not in wire_text(request) for request in observed)
    assert "<your-api-key>" in wire_text(server.main_requests()[0])
