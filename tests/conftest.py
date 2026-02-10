import pytest
from pathlib import Path
import tempfile


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
