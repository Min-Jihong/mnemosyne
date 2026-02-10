import os
import pytest
from pathlib import Path
import tempfile


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests requiring browser")
    config.addinivalue_line("markers", "live: Tests requiring real LLM API calls")
    config.addinivalue_line("markers", "slow: Tests taking >10 seconds")
    config.addinivalue_line("markers", "integration: Integration tests")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on markers and environment."""
    skip_e2e = pytest.mark.skip(reason="E2E tests disabled (set MNEMOSYNE_E2E_TEST=1)")
    skip_live = pytest.mark.skip(reason="Live tests disabled (set MNEMOSYNE_LIVE_TEST=1)")

    for item in items:
        if "e2e" in item.keywords and not os.environ.get("MNEMOSYNE_E2E_TEST"):
            item.add_marker(skip_e2e)
        if "live" in item.keywords and not os.environ.get("MNEMOSYNE_LIVE_TEST"):
            item.add_marker(skip_live)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_events():
    from mnemosyne.capture.events import (
        MouseClickEvent,
        KeyPressEvent,
        WindowChangeEvent,
    )
    import time
    
    base_time = time.time()
    
    return [
        WindowChangeEvent(
            timestamp=base_time,
            app_name="Safari",
            window_title="Google",
            bundle_id="com.apple.Safari",
        ),
        MouseClickEvent(
            timestamp=base_time + 1,
            x=100,
            y=200,
            button="left",
            pressed=True,
        ),
        KeyPressEvent(
            timestamp=base_time + 2,
            key="a",
            key_char="a",
            modifiers=[],
        ),
    ]
