# Recording Guide

Learn how to capture your computer activity with Mnemosyne.

## Overview

Mnemosyne records your micro-actions with millisecond precision:

- **Mouse** - Position, clicks, double-clicks, drag, scroll, hover time
- **Keyboard** - Key presses, hotkeys, typing patterns
- **Screen** - Automatic screenshots on significant actions
- **Context** - Active app, window title, URL, file path

## Starting a Recording

### CLI

```bash
# Basic recording
mnemosyne record

# Named session
mnemosyne record --name "Work Session"

# With screenshot interval
mnemosyne record --screenshot-interval 60
```

### Web Interface

1. Open [http://localhost:8000](http://localhost:8000)
2. Click **Start Recording**
3. Click **Stop Recording** when done

### Programmatic

```python
from mnemosyne.capture import RecordingSession

async with RecordingSession("My Session") as session:
    await session.wait_until_stopped()
```

## What Gets Captured

### Mouse Events

| Event | Data Captured |
|-------|--------------|
| Move | Position (x, y), timestamp |
| Click | Position, button, target element |
| Double-click | Position, button |
| Scroll | Direction, amount, position |
| Drag | Start/end positions |

### Keyboard Events

| Event | Data Captured |
|-------|--------------|
| Key press | Key, modifiers, timestamp |
| Key release | Key, timestamp |
| Hotkey | Combination (e.g., Cmd+C) |
| Typed text | Full text (configurable) |

### Screenshots

Captured automatically on:

- Mouse clicks
- Hotkey combinations
- App/window switches
- Configurable intervals

## Privacy Considerations

!!! warning "Sensitive Data"
    Mnemosyne captures everything. Be mindful of:

    - **Passwords** - Disable `track_typing` if concerned
    - **Sensitive apps** - Add to `blocked_apps`
    - **Screen content** - Screenshots may capture private data

### Configuring Privacy

```toml
[recording]
# Disable text capture
track_typing = false

# Skip screenshots in sensitive apps
# (Configure in execution.blocked_apps)
```

## Managing Sessions

### List Sessions

```bash
mnemosyne sessions
```

### Export Session

```bash
mnemosyne export <session_id> --format json
```

### Delete Session

```bash
mnemosyne delete <session_id>
```

## Best Practices

1. **Name your sessions** - Makes them easier to find later
2. **Record focused work** - Shorter, purposeful sessions work better
3. **Review periodically** - Delete sessions with sensitive data
4. **Configure blocklist** - Add sensitive apps to `blocked_apps`
