"""Pytest entry point for the optional Aero live WebApp smoke."""
import os

import pytest


def test_webapp_renders_visualcards_directive():
    if os.environ.get("AERO_LIVE_SMOKE") != "1":
        pytest.skip("requires a running WebApp with CDP on 127.0.0.1:9222")
    import live_webapp_smoke

    assert live_webapp_smoke.main() == 0
