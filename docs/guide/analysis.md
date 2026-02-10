# Analysis Guide

Understand your behavior with Mnemosyne's AI analysis.

## Overview

Mnemosyne doesn't just record—it understands. The analysis system:

1. **Infers intent** - Why did you perform each action?
2. **Asks questions** - What patterns need explanation?
3. **Generates insights** - What can we learn from your behavior?

## Running Analysis

### Basic Analysis

```bash
mnemosyne analyze <session_id>
```

This runs intent inference on all actions in the session.

### Curious Analysis

```bash
mnemosyne curious <session_id>
```

The AI generates questions about your behavior:

```
🤔 Questions about your session:

1. [HIGH] Why do you always open Slack before checking email?
   Category: workflow | Confidence: 89%

2. [MEDIUM] You typed "git status" 23 times but only committed 3 times.
   Category: habit | Confidence: 72%

3. [HIGH] There's a consistent 2-second pause before switching to Terminal.
   Category: decision | Confidence: 85%
```

## Curiosity Modes

### Passive

AI only answers questions, never asks.

```toml
[curiosity]
mode = "passive"
```

### Active

AI asks questions after analyzing sessions.

```toml
[curiosity]
mode = "active"
```

### Proactive

AI is constantly curious, even during recording.

```toml
[curiosity]
mode = "proactive"
```

## Question Categories

| Category | Description |
|----------|-------------|
| `workflow` | Process and sequence patterns |
| `habit` | Repeated unconscious behaviors |
| `decision` | Hesitation or choice points |
| `efficiency` | Potential optimizations |
| `anomaly` | Unusual behaviors |

## Understanding Scores

### Confidence

How sure the AI is about the observation (0-100%).

### Importance

How significant the pattern is for learning (0-100%).

## Answering Questions

When the AI asks questions, your answers help it learn:

```bash
mnemosyne answer <question_id> "I check Slack first to see if anything urgent happened overnight"
```

These answers are stored in memory and inform future analysis.

## Programmatic Analysis

```python
from mnemosyne.reason import CuriousLLM, IntentInference

# Initialize
curious = CuriousLLM(llm_provider)
intent = IntentInference(llm_provider)

# Analyze events
questions = await curious.observe_and_wonder(events)
intents = await intent.infer_batch(events)

# Generate summary
summary = await curious.generate_summary(events, intents)
```

## Tips for Better Analysis

1. **Record longer sessions** - More data = better patterns
2. **Be consistent** - Regular recording builds understanding
3. **Answer questions** - Your explanations improve accuracy
4. **Use proactive mode** - Get real-time insights
