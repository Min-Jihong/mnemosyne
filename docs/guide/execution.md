# Execution Guide

Let your digital twin take action on your behalf.

## Overview

The execution agent can control your computer based on learned behaviors. It's designed with safety as the top priority.

!!! warning "Use with Caution"
    The execution agent can interact with your computer. Always enable confirmation mode for sensitive tasks.

## Running Executions

### CLI

```bash
# With confirmation (recommended)
mnemosyne execute "Set up my usual coding environment" --confirm

# Without confirmation (careful!)
mnemosyne execute "Open my email"
```

### Web Interface

Chat with your digital twin:

> "Can you set up my morning work environment?"

## Safety Features

### Rate Limiting

```toml
[execution]
max_actions_per_minute = 60
cooldown_between_actions_ms = 100
```

### Blocked Applications

Never interacts with sensitive apps:

```toml
[execution]
blocked_apps = [
    "1Password",
    "Keychain Access",
    "System Preferences",
    "Terminal",
]
```

### Blocked Hotkeys

Prevents dangerous shortcuts:

```toml
[execution]
blocked_hotkeys = [
    ["cmd", "q"],
    ["cmd", "shift", "q"],
    ["cmd", "option", "esc"],
]
```

### Safe Zones

Restrict actions to screen regions:

```toml
[execution]
# Only allow actions in this region
safe_zone = { x = 0, y = 0, width = 1920, height = 1080 }
```

### Confirmation Mode

Always ask before executing:

```toml
[execution]
require_confirmation = true
```

## Emergency Stop

If something goes wrong:

1. **Keyboard**: Press `Ctrl+C` in terminal
2. **Physical**: Move mouse rapidly to corners
3. **Force quit**: `Cmd+Option+Esc` on macOS

## How It Works

1. **Goal Interpretation** - AI understands what you want
2. **Plan Generation** - Creates sequence of actions
3. **Safety Check** - Validates against blocklists
4. **Execution** - Performs actions with delays
5. **Verification** - Confirms expected outcomes

## Execution Modes

### Demonstration

Shows what would happen without doing it:

```bash
mnemosyne execute "..." --dry-run
```

### Confirmation

Asks before each action:

```bash
mnemosyne execute "..." --confirm
```

### Autonomous

Executes without confirmation (careful!):

```bash
mnemosyne execute "..."
```

## Programmatic Control

```python
from mnemosyne.execute import ExecutionAgent

agent = ExecutionAgent(llm_provider)

# Plan without executing
plan = await agent.plan("Open my email client")
print(plan.actions)

# Execute with confirmation
result = await agent.execute(plan, confirm=True)

# Emergency stop
agent.stop()
```

## Best Practices

1. **Start with dry-run** - See what would happen first
2. **Use confirmation mode** - Especially for new tasks
3. **Configure blocklists** - Add sensitive apps
4. **Monitor execution** - Watch what's happening
5. **Have emergency stop ready** - Know how to intervene
