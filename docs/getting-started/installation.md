# Installation

This guide covers installing Mnemosyne on your system.

## Requirements

- **Python 3.11+** (3.12 recommended)
- **macOS** (primary support) or Linux
- **Permissions** (macOS): Accessibility, Input Monitoring, Screen Recording

## Quick Install

### Using pip (Recommended)

```bash
pip install mnemosyne
```

### Using uv (Faster)

```bash
uv pip install mnemosyne
```

### From Source

```bash
git clone https://github.com/Min-Jihong/mnemosyne.git
cd mnemosyne
pip install -e ".[all]"
```

## Installation Options

Mnemosyne uses optional dependencies for different features:

| Extra | Features | Command |
|-------|----------|---------|
| `web` | Web interface, REST API | `pip install mnemosyne[web]` |
| `macos` | Native macOS capture | `pip install mnemosyne[macos]` |
| `ml` | Training capabilities | `pip install mnemosyne[ml]` |
| `dev` | Development tools | `pip install mnemosyne[dev]` |
| `all` | Everything | `pip install mnemosyne[all]` |

## macOS Permissions

Mnemosyne needs these permissions to observe your behavior:

### Grant Permissions

1. **System Settings** → **Privacy & Security**

2. **Accessibility**
   - Add your terminal (Terminal, iTerm2, VS Code)
   - Required for: Mouse and keyboard capture

3. **Input Monitoring**
   - Add your terminal
   - Required for: Keyboard events

4. **Screen Recording**
   - Add your terminal
   - Required for: Screenshots

!!! warning "Permission Denied?"
    If you get permission errors, make sure to:

    1. Quit and restart your terminal
    2. Check all three permission categories
    3. Run the app from a location with permissions

## Verify Installation

```bash
# Check version
mnemosyne version

# Run setup wizard
mnemosyne setup

# Check status
mnemosyne status
```

## Troubleshooting

### Python Version

```bash
python --version  # Should be 3.11+
```

If you have multiple Python versions:

```bash
python3.11 -m pip install mnemosyne
```

### Virtual Environment

We recommend using a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install mnemosyne[all]
```

### macOS: pyobjc Issues

If you encounter pyobjc errors:

```bash
pip install --upgrade pyobjc-core pyobjc-framework-Quartz pyobjc-framework-AppKit
```

### Linux: X11 Requirements

On Linux, you may need:

```bash
sudo apt-get install python3-xlib xdotool  # Debian/Ubuntu
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started in 5 minutes
- [Configuration](configuration.md) - Customize Mnemosyne
