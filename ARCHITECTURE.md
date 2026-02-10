# Mnemosyne Architecture

> "Learn to Think Like You" - 당신의 컴퓨터 행동을 학습하여 당신처럼 사고하는 디지털 트윈

## Overview

Mnemosyne는 사용자의 모든 컴퓨터 행동을 마이크로 레벨까지 기록하고, LLM을 통해 "왜 이 행동을 했는가"를 추론하여, 궁극적으로 사용자의 사고 패턴을 학습하는 시스템입니다.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MNEMOSYNE PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌───────┐ │
│  │ CAPTURE  │──▶│  STORE   │──▶│  REASON  │──▶│  LEARN   │──▶│EXECUTE│ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └───────┘ │
│       │              │              │              │              │     │
│       ▼              ▼              ▼              ▼              ▼     │
│   Mouse/Key      SQLite +       LLM Intent      Action        Computer │
│   Screen/Win     Screenshots    Inference     Transformer      Control │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Principles

1. **Micro-Level Recording**: 마우스 좌표, 키 입력, 타이밍까지 모든 것을 기록
2. **Context is King**: 행동만이 아닌, 그 순간의 화면/윈도우/앱 컨텍스트를 함께 저장
3. **Intent Inference**: LLM이 "왜"를 추론하여 의미 있는 학습 데이터로 변환
4. **Behavioral Cloning**: 단순 매크로가 아닌, 상황에 맞는 적응적 행동 학습
5. **Curious LLM**: LLM이 수동적으로 답하는 게 아니라, 능동적으로 질문하고 패턴을 탐색
6. **Persistent Memory**: 모든 사용자 명령과 대화를 영구 기억하여 장기적 맥락 유지

## Phase 1: Capture Layer

### Components

| Module | Purpose | Technology |
|--------|---------|------------|
| `mouse.py` | 마우스 이동, 클릭, 스크롤 캡처 | pynput |
| `keyboard.py` | 키 입력, 단축키, 텍스트 타이핑 | pynput |
| `screen.py` | 스크린샷 캡처 (효율적 압축) | Quartz (macOS) |
| `window.py` | 활성 윈도우, 앱 정보 | AppKit, Accessibility API |
| `recorder.py` | 전체 캡처 오케스트레이션 | asyncio |

### Data Flow

```
User Action
    │
    ├──▶ MouseListener ──▶ MouseEvent(x, y, button, action_type, timestamp)
    │
    ├──▶ KeyboardListener ──▶ KeyEvent(key, modifiers, timestamp)
    │
    ├──▶ ScreenCapture ──▶ Screenshot(image_data, timestamp) [throttled]
    │
    └──▶ WindowMonitor ──▶ WindowState(app, title, bounds)
    
    All merged into ──▶ MicroAction(event + context)
```

### Event Types

```python
class ActionType(Enum):
    # Mouse
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_SCROLL = "mouse_scroll"
    
    # Keyboard
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    KEY_TYPE = "key_type"      # Aggregated typing
    HOTKEY = "hotkey"          # Cmd+C, Ctrl+V, etc.
```

## Phase 2: Store Layer

### Database Schema

```sql
-- Sessions: 녹화 세션
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at REAL NOT NULL,
    ended_at REAL,
    description TEXT,
    metadata JSON
);

-- Actions: 개별 행동
CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    duration_ms REAL,
    action_type TEXT NOT NULL,
    
    -- Mouse
    mouse_x INTEGER,
    mouse_y INTEGER,
    mouse_dx INTEGER,
    mouse_dy INTEGER,
    mouse_button TEXT,
    
    -- Keyboard
    key_name TEXT,
    key_char TEXT,
    key_code INTEGER,
    modifiers JSON,
    text TEXT,
    
    -- Context
    screenshot_id TEXT,
    window_title TEXT,
    window_bounds JSON,
    active_app TEXT,
    
    -- LLM Inference (filled later)
    inferred_intent TEXT,
    reasoning TEXT,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id)
);

-- Screenshots: 스크린샷 메타데이터
CREATE TABLE screenshots (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    filepath TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### Storage Strategy

- **Screenshots**: WebP 포맷 (80% 품질), 필요시만 캡처 (액션 발생 시)
- **Actions**: SQLite with WAL mode (고속 쓰기)
- **Compression**: 세션 종료 후 배치 압축

## Phase 3: Reason Layer

### LLM Intent Inference

각 행동에 대해 LLM이 "왜"를 추론:

```python
# Input to LLM
{
    "screenshot": <base64 image>,
    "action": {
        "type": "mouse_click",
        "x": 1200, "y": 450,
        "window": "VS Code",
        "element_near_cursor": "Save button"
    },
    "previous_actions": [...last 5 actions...],
    "task_context": "Working on Python project"
}

# LLM Output
{
    "intent": "save_file",
    "reasoning": "User clicked the Save button after making edits to main.py, likely to persist changes before running the code.",
    "confidence": 0.92,
    "semantic_action": "SAVE_CURRENT_FILE"
}
```

### Prompt Strategy (Chain-of-Thought)

```
1. 현재 화면 분석: 어떤 앱에서 무엇을 보고 있는가?
2. 이전 행동 분석: 직전 5개 행동의 맥락은?
3. 클릭/타이핑 위치: 어떤 UI 요소인가?
4. 의도 추론: 왜 이 행동을 했을까?
5. 시맨틱 액션: 고수준 행동으로 분류
```

## Phase 4: Learn Layer

### Action Chunking Transformer (ACT)

```
Input: (screenshot, window_state, recent_actions, task_description)
   │
   ▼
┌─────────────────────────────────────────┐
│           Vision Encoder                │
│    (ResNet/ViT for screenshot)          │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│         Context Encoder                 │
│  (Transformer for action history)       │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│         Action Decoder                  │
│  (Predict next K actions as chunk)      │
└─────────────────────────────────────────┘
   │
   ▼
Output: [action_1, action_2, ..., action_K]
```

### Training Data Format

```python
{
    "observation": {
        "screenshot": "path/to/screenshot.webp",
        "window": {"app": "Chrome", "title": "GitHub"},
        "history": [... last 10 actions with intents ...]
    },
    "task": "Create a new repository",
    "action_chunk": [
        {"type": "click", "x": 100, "y": 50, "intent": "click_new_button"},
        {"type": "type", "text": "my-repo", "intent": "enter_repo_name"},
        {"type": "click", "x": 200, "y": 400, "intent": "confirm_creation"}
    ]
}
```

## Phase 5: Execute Layer

### Agent Architecture

```
┌─────────────────────────────────────────┐
│              AGENT LOOP                 │
├─────────────────────────────────────────┤
│                                         │
│  1. Observe: Capture current screen     │
│       │                                 │
│       ▼                                 │
│  2. Think: Model predicts action chunk  │
│       │                                 │
│       ▼                                 │
│  3. Act: Execute first action           │
│       │                                 │
│       ▼                                 │
│  4. Verify: Check if expected result    │
│       │                                 │
│       └──▶ Loop until task complete     │
│                                         │
└─────────────────────────────────────────┘
```

### Safety Mechanisms

1. **Allowlist Mode**: 특정 앱/영역만 제어 허용
2. **Confirmation**: 위험 행동 (파일 삭제 등) 전 확인
3. **Kill Switch**: 즉시 중단 단축키 (Cmd+Shift+Esc)
4. **Sandbox**: 초기에는 가상 환경에서만 실행

## Technology Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python 3.11+ | ML 생태계, macOS API 지원 |
| Input Capture | pynput | 크로스플랫폼, 안정적 |
| Screen Capture | Quartz (macOS) | 네이티브 고성능 |
| Database | SQLite | 단일 파일, 빠른 쓰기 |
| Vector Store | ChromaDB | 로컬 임베딩, 시맨틱 검색 |
| LLM | Multi-Provider | OpenAI, Anthropic, Google (사용자 선택) |
| ML Framework | PyTorch | ACT 모델 구현 |
| Execution | pyautogui | 크로스플랫폼 자동화 |

## LLM Provider System (Multi-Provider Support)

OpenClaw처럼 사용자가 원하는 LLM 프로바이더를 선택하여 설정할 수 있는 시스템.

### Supported Providers

| Provider | Models | Vision | Embedding | Setup |
|----------|--------|--------|-----------|-------|
| **OpenAI** | GPT-4o, GPT-4-turbo, GPT-4o-mini | Yes | text-embedding-3-* | API Key |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus/Haiku | Yes | (via Voyage) | API Key |
| **Google** | Gemini 1.5 Pro, Gemini 1.5 Flash | Yes | text-embedding-004 | API Key |
| **Ollama** | Llama 3, Mistral, etc. | Llava | nomic-embed-text | Local |
| **Custom** | Any OpenAI-compatible API | Varies | Varies | Base URL + Key |

### Configuration Flow (Interactive Setup)

```
$ mnemosyne setup

🧠 Mnemosyne Setup

Step 1/4: LLM Provider
────────────────────────
Choose your LLM provider:
  [1] OpenAI (GPT-4o, GPT-4-turbo)
  [2] Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
  [3] Google (Gemini 1.5 Pro, Gemini 1.5 Flash)
  [4] Ollama (Local - Llama 3, Mistral)
  [5] Custom (OpenAI-compatible API)

> 2

Step 2/4: API Key
────────────────────────
Enter your Anthropic API key:
> sk-ant-xxxxx

Verifying... ✓ Valid

Step 3/4: Model Selection
────────────────────────
Choose your primary model:
  [1] claude-3-5-sonnet-20241022 (Recommended - Best balance)
  [2] claude-3-opus-20240229 (Most capable)
  [3] claude-3-haiku-20240307 (Fastest, cheapest)

> 1

Step 4/4: Embedding Provider
────────────────────────
Choose embedding provider for memory search:
  [1] OpenAI (text-embedding-3-small) - Requires OpenAI key
  [2] Voyage AI (voyage-3) - Optimized for Claude
  [3] Local (nomic-embed-text via Ollama) - No API needed
  [4] Same as LLM provider (if supported)

> 3

✅ Setup complete! Configuration saved to ~/.mnemosyne/config.toml
```

### Configuration File (~/.mnemosyne/config.toml)

```toml
[llm]
provider = "anthropic"
model = "claude-3-5-sonnet-20241022"
api_key_env = "ANTHROPIC_API_KEY"  # Reference to env var
# api_key = "sk-ant-xxx"  # Or direct (not recommended)

# Vision model (for screenshot analysis)
[llm.vision]
provider = "anthropic"  # Can be different from main
model = "claude-3-5-sonnet-20241022"

# Lightweight model for simple tasks
[llm.fast]
provider = "anthropic"
model = "claude-3-haiku-20240307"

[embedding]
provider = "ollama"
model = "nomic-embed-text"
# base_url = "http://localhost:11434"  # For Ollama

# Alternative: OpenAI embeddings
# [embedding]
# provider = "openai"
# model = "text-embedding-3-small"
# api_key_env = "OPENAI_API_KEY"

[memory]
db_path = "~/.mnemosyne/memory.db"
vector_db_path = "~/.mnemosyne/chroma"
consolidation_interval = "daily"  # When to run memory consolidation

[capture]
screenshot_quality = 80
screenshot_format = "webp"
excluded_apps = ["1Password", "Keychain Access", "Banking App"]

[curiosity]
mode = "curious"  # passive, curious, interactive, proactive
```

### Provider Interface (Unified API)

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class LLMProvider(ABC):
    """Base class for all LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        **kwargs
    ) -> Response:
        """Generate a completion."""
        pass
    
    @abstractmethod
    async def complete_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        model: str | None = None,
        **kwargs
    ) -> Response:
        """Generate completion with image understanding."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        pass


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
```

### Provider Implementations

```python
# mnemosyne/llm/providers/anthropic.py
class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def complete_with_vision(self, messages, images, model=None, **kwargs):
        # Convert images to base64 for Claude
        image_content = [
            {"type": "image", "source": {"type": "base64", "data": b64encode(img)}}
            for img in images
        ]
        # ... implementation

# mnemosyne/llm/providers/openai.py
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str | None = None):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    # ... implementation

# mnemosyne/llm/providers/google.py
class GoogleProvider(LLMProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
    
    # ... implementation

# mnemosyne/llm/providers/ollama.py
class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    # ... implementation (no API key needed)
```

### Factory Pattern for Provider Creation

```python
# mnemosyne/llm/factory.py
from mnemosyne.config import Config

def create_llm_provider(config: Config) -> LLMProvider:
    """Create LLM provider based on config."""
    provider_type = config.llm.provider
    
    match provider_type:
        case "openai":
            return OpenAIProvider(
                api_key=config.get_api_key("openai"),
                base_url=config.llm.get("base_url")
            )
        case "anthropic":
            return AnthropicProvider(
                api_key=config.get_api_key("anthropic")
            )
        case "google":
            return GoogleProvider(
                api_key=config.get_api_key("google")
            )
        case "ollama":
            return OllamaProvider(
                base_url=config.llm.get("base_url", "http://localhost:11434")
            )
        case _:
            raise ValueError(f"Unknown provider: {provider_type}")

def create_embedding_provider(config: Config) -> EmbeddingProvider:
    """Create embedding provider based on config."""
    # Similar pattern
    ...
```

### Environment Variables Support

```bash
# .env or shell exports
export ANTHROPIC_API_KEY="sk-ant-xxx"
export OPENAI_API_KEY="sk-xxx"
export GOOGLE_API_KEY="xxx"

# Config references these:
# api_key_env = "ANTHROPIC_API_KEY"
```

### Runtime Provider Switching

```python
# Can switch providers at runtime for different tasks
async def analyze_screenshot(screenshot: bytes) -> str:
    # Use vision-capable model
    provider = get_provider("vision")
    return await provider.complete_with_vision(
        messages=[{"role": "user", "content": "What's happening in this screenshot?"}],
        images=[screenshot]
    )

async def quick_classification(text: str) -> str:
    # Use fast model for simple tasks
    provider = get_provider("fast")
    return await provider.complete(
        messages=[{"role": "user", "content": f"Classify: {text}"}]
    )
```

## Data Privacy & Security

- **Local First**: 모든 데이터는 로컬에만 저장
- **Encryption**: 민감 데이터 (비밀번호 입력 등) 자동 마스킹
- **Opt-out Apps**: 특정 앱 (은행, 비밀번호 관리자) 녹화 제외
- **Data Retention**: 설정 가능한 자동 삭제 주기

## Phase 6: Memory Layer (Persistent Memory)

OpenClaw처럼 모든 사용자 명령과 대화를 영구 기억하는 시스템.

### Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEMORY SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│  │  Episodic   │   │  Semantic   │   │ Procedural  │                   │
│  │   Memory    │   │   Memory    │   │   Memory    │                   │
│  └─────────────┘   └─────────────┘   └─────────────┘                   │
│        │                 │                 │                            │
│        ▼                 ▼                 ▼                            │
│   개별 이벤트         추출된 지식       학습된 패턴                      │
│   (명령, 대화)       (사실, 선호도)     (행동 시퀀스)                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Vector Store (Embeddings)                      │  │
│  │              ChromaDB / Qdrant (Semantic Search)                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Memory Types

| Type | 저장 내용 | 검색 방식 | 예시 |
|------|----------|----------|------|
| **Episodic** | 구체적 이벤트, 명령, 대화 | 시간순 + 시맨틱 | "어제 GitHub에서 뭘 했지?" |
| **Semantic** | 추출된 사실, 선호도, 지식 | 시맨틱 검색 | "내가 선호하는 코딩 스타일은?" |
| **Procedural** | 반복된 행동 패턴, 워크플로우 | 컨텍스트 매칭 | "PR 올릴 때 항상 하는 순서" |

### Database Schema (Memory)

```sql
-- Episodic Memory: 모든 명령과 대화
CREATE TABLE episodic_memory (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    type TEXT NOT NULL,  -- 'command', 'conversation', 'observation'
    content TEXT NOT NULL,
    context JSON,  -- 당시 상황 (앱, 작업 등)
    embedding BLOB,  -- Vector embedding for semantic search
    importance REAL DEFAULT 0.5,  -- 중요도 (0-1)
    access_count INTEGER DEFAULT 0,
    last_accessed REAL
);

-- Semantic Memory: 추출된 지식
CREATE TABLE semantic_memory (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,  -- 'preference', 'fact', 'skill', 'relationship'
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    source_episodes JSON,  -- 이 지식이 추출된 에피소드들
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    embedding BLOB
);

-- Procedural Memory: 행동 패턴
CREATE TABLE procedural_memory (
    id TEXT PRIMARY KEY,
    name TEXT,  -- 패턴 이름 (자동 또는 사용자 지정)
    trigger_context JSON,  -- 이 패턴이 활성화되는 조건
    action_sequence JSON,  -- 행동 시퀀스
    frequency INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 1.0,
    last_used REAL,
    embedding BLOB
);
```

### Memory Operations

```python
class MemorySystem:
    async def remember(self, event: MemoryEvent) -> str:
        """새로운 이벤트를 기억"""
        
    async def recall(self, query: str, limit: int = 10) -> List[Memory]:
        """관련 기억 검색 (시맨틱 + 시간 가중치)"""
        
    async def consolidate(self) -> None:
        """에피소드 → 시맨틱 메모리 변환 (수면 중 기억 정리처럼)"""
        
    async def forget(self, criteria: ForgetCriteria) -> int:
        """중요도 낮은 기억 정리 (선택적)"""
        
    async def extract_knowledge(self, episodes: List[Episode]) -> List[SemanticFact]:
        """에피소드에서 시맨틱 지식 추출"""
```

### Memory Consolidation (기억 정리)

주기적으로 에피소드 메모리를 분석하여 시맨틱/프로시저럴 메모리로 변환:

```python
# 예: 반복 패턴 감지
episodes = await memory.get_recent(hours=24)
patterns = await llm.analyze_patterns(episodes)

# "사용자는 항상 커밋 전에 테스트를 실행한다"
await memory.store_semantic(
    category="preference",
    subject="user",
    predicate="always_does_before_commit",
    object="run_tests",
    confidence=0.85
)
```

## Phase 7: Curious LLM (능동적 탐구)

LLM이 수동적으로 "왜?"에만 답하는 게 아니라, 능동적으로 질문하고 탐구하는 시스템.

### Curiosity Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CURIOUS LLM ENGINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────┐                                                     │
│  │ Pattern Detector│──▶ "이 행동이 평소와 다르네?"                       │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  ┌────────────────┐                                                     │
│  │Question Generator│──▶ "왜 오늘은 다른 방식으로 했을까?"              │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  ┌────────────────┐                                                     │
│  │Hypothesis Engine│──▶ "아마 새 라이브러리를 테스트 중인 것 같다"      │
│  └────────────────┘                                                     │
│           │                                                             │
│           ▼                                                             │
│  ┌────────────────┐                                                     │
│  │ Verification   │──▶ 가설 검증 (추가 관찰 or 사용자 질문)             │
│  └────────────────┘                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Curiosity Triggers

| Trigger | 설명 | LLM 질문 예시 |
|---------|------|--------------|
| **Anomaly** | 평소 패턴과 다른 행동 | "보통 Cmd+S로 저장하는데, 왜 메뉴를 클릭했지?" |
| **New Pattern** | 처음 보는 행동 시퀀스 | "이 앱은 처음 쓰는 것 같은데, 뭐하는 앱이지?" |
| **Inefficiency** | 비효율적 반복 | "같은 작업을 3번 반복했는데, 자동화할 수 있을까?" |
| **Gap** | 이해 못한 부분 | "왜 갑자기 터미널을 열었지? 맥락이 안 보인다" |
| **Contradiction** | 이전 패턴과 모순 | "평소엔 테스트 먼저 하는데, 왜 오늘은 바로 커밋?" |

### Curiosity Modes

```python
class CuriosityMode(Enum):
    PASSIVE = "passive"      # 관찰만, 질문 안 함
    CURIOUS = "curious"      # 내부적으로 질문 생성, 사용자에게 묻지 않음
    INTERACTIVE = "interactive"  # 궁금하면 사용자에게 직접 질문
    PROACTIVE = "proactive"  # 적극적으로 제안 ("이거 자동화할까요?")
```

### Curiosity Questions Storage

```sql
CREATE TABLE curiosity_log (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    trigger_type TEXT NOT NULL,  -- anomaly, new_pattern, etc.
    trigger_context JSON,  -- 트리거된 상황
    question TEXT NOT NULL,  -- 생성된 질문
    hypothesis TEXT,  -- LLM의 가설
    resolution TEXT,  -- 해결 (answered, inferred, asked_user)
    answer TEXT,  -- 답변 (있을 경우)
    learned_fact TEXT  -- 이로부터 학습한 것
);
```

### Interactive Curiosity Flow

```python
# 이상 행동 감지 시
if curiosity_mode == CuriosityMode.INTERACTIVE:
    question = await llm.generate_question(anomaly)
    
    # 적절한 타이밍에 사용자에게 질문 (작업 중단 최소화)
    if user_seems_idle():
        answer = await ask_user(question)
        await memory.store_qa(question, answer)
    else:
        # 나중에 물어보기 위해 큐에 저장
        await curiosity_queue.add(question)
```

### Learning from Curiosity

호기심 → 질문 → 답변 → 지식 추출 사이클:

```
1. 관찰: 사용자가 VS Code에서 Vim 모드를 켰다
2. 질문: "왜 갑자기 Vim 모드를 쓰기 시작했지?"
3. 가설: "생산성 향상을 위해 새 도구를 배우는 중일 수도"
4. (Interactive 모드) 사용자에게 질문
5. 답변: "팀에서 Vim 쓰는 사람이 많아서 배워보려고"
6. 학습: semantic_memory에 저장
   - subject: "user"
   - predicate: "is_learning"
   - object: "vim_for_team_collaboration"
```

## Updated Pipeline (with Memory + Curiosity)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MNEMOSYNE FULL PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │CAPTURE │─▶│ STORE  │─▶│ REASON │─▶│ LEARN  │─▶│EXECUTE │─▶│FEEDBACK│   │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │
│       │           │           │           │           │           │         │
│       │           │           │           │           │           │         │
│       │           ▼           ▼           │           │           │         │
│       │      ┌─────────────────────┐      │           │           │         │
│       └─────▶│      MEMORY         │◀─────┴───────────┴───────────┘         │
│              │  (Episodic/Semantic/│                                        │
│              │    Procedural)      │                                        │
│              └─────────────────────┘                                        │
│                        │                                                    │
│                        ▼                                                    │
│              ┌─────────────────────┐                                        │
│              │   CURIOUS LLM       │                                        │
│              │  (Questions/Hypo/   │                                        │
│              │   Verification)     │                                        │
│              └─────────────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Future Enhancements

1. **Multi-modal Input**: 음성 명령, 제스처 인식
2. **Collaborative Learning**: 여러 사용자 패턴 통합 (opt-in)
3. **Real-time Coaching**: 작업 중 힌트 제공
4. **Cross-device Sync**: 여러 기기 간 학습 데이터 동기화
5. **Dream Mode**: 수면/유휴 시간에 기억 정리 및 패턴 최적화
6. **Personality Evolution**: 시간이 지나며 사용자 성향에 맞게 LLM 성격 조정
