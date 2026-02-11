# Awesome Lists Registration Guide

This document provides templates for submitting Mnemosyne to various "Awesome" lists on GitHub.

---

## Target Lists

| List | Repository | Category | Priority |
|------|------------|----------|----------|
| awesome-python | vinta/awesome-python | Automation / Machine Learning | High |
| awesome-machine-learning | josephmisiti/awesome-machine-learning | Python | High |
| awesome-macos | iCHAIT/awesome-macOS | Productivity | Medium |
| awesome-privacy | pluja/awesome-privacy | Desktop | Medium |
| awesome-llm | Hannibal046/Awesome-LLM | Tools | Medium |
| awesome-selfhosted | awesome-selfhosted/awesome-selfhosted | Automation | Low |

---

## PR Templates

### awesome-python (vinta/awesome-python)

**PR Title:**
```
Add Mnemosyne to Machine Learning / Automation
```

**PR Body:**
```markdown
## Checklist
- [x] Link to the project is included
- [x] Project has a clear README
- [x] Project is actively maintained
- [x] Project is stable

## Addition

### In section: Machine Learning (or Automation)

[Mnemosyne](https://github.com/Min-Jihong/mnemosyne) - A digital twin that learns how you think by recording micro-actions and asking "Why?" with AI-powered intent inference. Supports OpenAI, Anthropic, Google, and Ollama.

## Why?

Mnemosyne is unique because it:
- Captures **intent**, not just actions
- Uses a "Curious AI" that asks questions about user behavior
- Provides OCR search across screenshots
- Supports multiple LLM providers
- Is privacy-first with local storage
```

---

### awesome-machine-learning (josephmisiti/awesome-machine-learning)

**PR Title:**
```
Add Mnemosyne - Behavioral Cloning Digital Twin
```

**PR Body:**
```markdown
## Checklist
- [x] I have read the [contributing guidelines](CONTRIBUTING.md)
- [x] The project is open source
- [x] The project has at least 100 stars (or explain why it should be included)

## Addition

### In section: Python / General-Purpose Machine Learning

* [Mnemosyne](https://github.com/Min-Jihong/mnemosyne) - Digital twin that learns user thought patterns through behavioral cloning with AI intent inference, OCR search, and multi-LLM support.

## Description

Mnemosyne records computer micro-actions (mouse, keyboard, screen) and uses LLMs to understand **why** users perform actions, not just **what** they do. It builds a semantic memory that enables action replay with inferred intent.

Key features:
- Micro-action recording with millisecond precision
- Curious AI questioning for intent inference
- OCR text search across screenshots
- ChromaDB for semantic memory
- Multi-LLM: OpenAI, Anthropic, Google, Ollama
```

---

### awesome-macos (iCHAIT/awesome-macOS)

**PR Title:**
```
Add Mnemosyne - AI-powered behavior recorder
```

**PR Body:**
```markdown
## Addition

### In section: Productivity

- [Mnemosyne](https://github.com/Min-Jihong/mnemosyne) - Digital twin that learns how you think by recording your behavior and asking "Why?" with AI. ![Open-Source Software][OSS Icon]

## Why?

- Native macOS integration using pyobjc
- Records mouse, keyboard, and screen with macOS APIs
- Privacy-first with local storage
- Free and open source (MIT license)
```

---

### awesome-privacy (pluja/awesome-privacy)

**PR Title:**
```
Add Mnemosyne - Privacy-first digital twin
```

**PR Body:**
```markdown
## Addition

### In section: Desktop / Productivity

- [Mnemosyne](https://github.com/Min-Jihong/mnemosyne) - Privacy-first digital twin that learns your computer behavior. All data stored locally with PII detection and scrubbing. Multi-LLM support including local Ollama.

## Privacy Features

- All data stored locally (no cloud)
- Automatic PII detection and redaction
- Works with local LLMs (Ollama)
- No telemetry or tracking
- MIT licensed, fully auditable
```

---

### awesome-llm (Hannibal046/Awesome-LLM)

**PR Title:**
```
Add Mnemosyne - Multi-LLM Digital Twin
```

**PR Body:**
```markdown
## Addition

### In section: LLM Applications / Productivity

| Name | Description | Link |
|------|-------------|------|
| Mnemosyne | Digital twin that learns user thought patterns through behavioral recording and LLM-powered intent inference | [GitHub](https://github.com/Min-Jihong/mnemosyne) |

## Description

Multi-provider LLM abstraction supporting:
- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic (Claude 3, Claude 3.5)
- Google (Gemini Pro, Gemini Ultra)
- Ollama (local models)

Unique "Curious AI" feature that uses LLMs to ask questions about user behavior for intent inference.
```

---

## Submission Checklist

Before submitting PRs:

- [ ] Read each repository's CONTRIBUTING.md
- [ ] Check if similar projects exist
- [ ] Ensure README is complete and professional
- [ ] Have at least some GitHub stars (for credibility)
- [ ] Project is stable and actively maintained
- [ ] Follow the exact format of existing entries
- [ ] Include all required checkboxes
- [ ] Be patient - reviews can take weeks

## Tips for Success

1. **Timing**: Submit during weekdays when maintainers are active
2. **Format**: Match the exact format of existing entries
3. **Concise**: Keep descriptions short and focused
4. **Unique**: Emphasize what makes Mnemosyne different
5. **Polite**: Be respectful and patient with maintainers
6. **Stars**: Having 100+ stars significantly increases acceptance rate

## After Submission

1. Respond promptly to any feedback
2. Make requested changes quickly
3. Thank maintainers regardless of outcome
4. If rejected, ask what improvements would help
