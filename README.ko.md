<div align="center">

# 🧠 Mnemosyne

### *또 하나의 나를 만들다*

**당신처럼 생각하는 법을 배우는 디지털 클론**

한국어 | [English](README.md) | [日本語](README.ja.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

---

## 🪞 디지털 자아의 꿈

> *누구나 한 번쯤 또 하나의 '나'를 만들고 싶다는 욕망을 품어본 적이 있습니다.*

내가 잠든 사이에도 일하는 나. 내가 지친 순간에도 생각하는 나. 내 습관을 알고, 내 선호를 이해하며, 나처럼 결정하는 또 하나의 존재.

**Mnemosyne**는 그 욕망을 현실로 만들기 위한 프로젝트입니다.

당신이 컴퓨터 앞에서 하는 모든 행동 — 마우스 클릭, 키보드 입력, 앱 전환, 스크롤 — 을 기록하고, AI가 **"왜 이 행동을 했을까?"**를 끊임없이 질문하며 학습합니다. 단순히 행동을 따라하는 것이 아니라, **당신의 사고방식 자체를 학습**합니다.

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│     "왜 거기를 클릭했나요?"                                        │
│     "앱을 전환할 때 무슨 생각이었나요?"                            │
│     "X를 하기 전에 항상 Y를 하시네요. 왜죠?"                       │
│                                                                    │
│                    — Mnemosyne, 당신처럼 되기 위해 배우는 중       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Mnemosyne가 다른 점

| 기존 자동화 도구 | Mnemosyne |
|-----------------|-----------|
| **무엇을** 했는지 기록 | **왜** 했는지 이해 |
| 고정된 스크립트 재생 | 새로운 상황에 적응 |
| 세션 간 기억 없음 | 모든 것을 영원히 기억 |
| 수동적인 도구 | 능동적으로 호기심 있는 AI |

---

## 🎯 주요 기능

### 📹 마이크로 액션 레코딩
밀리초 단위의 정밀도로 모든 상호작용을 캡처합니다:
- **마우스**: 위치, 클릭, 더블클릭, 드래그, 스크롤, 호버 시간
- **키보드**: 키 입력, 단축키, 타이핑 속도와 패턴
- **화면**: 중요한 행동 시 자동 스크린샷
- **컨텍스트**: 활성 앱, 윈도우 제목, URL, 파일 경로

### 🤔 호기심 있는 LLM
수동적인 기록 도구와 달리, Mnemosyne의 AI는 **진심으로 호기심이 있습니다**:

```python
# AI는 그냥 보기만 하지 않습니다 — 질문합니다
curiosities = await curious_llm.observe_and_wonder(events)

# 예시 출력:
# "왜 오늘 VS Code에서 Chrome으로 47번이나 전환했나요?"
# "글을 쓴 후 항상 위로 스크롤하시네요. 다시 읽는 건가요?"
# "매번 'git commit' 전에 3초간 멈추시네요. 망설임인가요?"
```

### 🧠 영구 메모리
잊지 않는 OpenClaw 스타일 메모리 시스템:
- **시맨틱 검색**: 키워드가 아닌 의미로 기억 찾기
- **메모리 통합**: 패턴에서 인사이트 자동 생성
- **벡터 저장소**: 빠른 검색을 위한 ChromaDB
- **장기 학습**: 수주, 수개월에 걸친 이해력 구축

### 🤖 실행 에이전트
디지털 트윈이 행동할 수 있습니다:
- 목표 지향적 컴퓨터 제어
- 안전 장치 (속도 제한, 차단된 앱, 긴급 정지)
- 신중한 실행을 위한 확인 모드
- 당신의 수정에서 학습

### 🔌 멀티 프로바이더 LLM 지원
신뢰하는 AI 프로바이더를 사용하세요:
- **OpenAI**: GPT-4, GPT-4 Turbo
- **Anthropic**: Claude 3, Claude 3.5
- **Google**: Gemini Pro, Gemini Ultra
- **Ollama**: Llama, Mistral 등 로컬 실행

### 🌐 웹 인터페이스
어디서든 디지털 트윈과 대화하세요:
- 자연어 상호작용을 위한 **모던 채팅 UI**
- 브라우저에서 **API 키 설정**
- **녹화 제어** 대시보드
- **메모리 검색** 인터페이스

---

## 🚀 빠른 시작

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/mnemosyne.git
cd mnemosyne

# pip으로 설치
pip install -e .

# 웹 인터페이스용
pip install -e ".[web]"

# macOS 네이티브 캡처용 (권장)
pip install -e ".[macos]"

# ML 학습 기능용
pip install -e ".[ml]"

# 모든 기능
pip install -e ".[all]"
```

### macOS 권한

Mnemosyne가 행동을 관찰하려면 다음 권한이 필요합니다:

| 권한 | 위치 | 이유 |
|------|------|------|
| **손쉬운 사용** | 시스템 설정 → 개인정보 보호 → 손쉬운 사용 | 마우스/키보드 캡처 |
| **입력 모니터링** | 시스템 설정 → 개인정보 보호 → 입력 모니터링 | 키보드 이벤트 |
| **화면 기록** | 시스템 설정 → 개인정보 보호 → 화면 기록 | 스크린샷 |

### 설정

```bash
mnemosyne setup
```

대화형 마법사가 다음을 구성합니다:
- 🔑 LLM 프로바이더 및 API 키
- 🤖 모델 선택
- 🧠 호기심 모드 (passive/active/proactive)

---

## 📖 사용법

### 웹 인터페이스 (권장)

```bash
# 웹 UI 시작
mnemosyne web

# 브라우저에서 http://localhost:8000 열기
```

웹 인터페이스에서 할 수 있는 것:
- 디지털 트윈과 채팅
- API 키로 LLM 설정 구성
- 녹화 세션 시작/중지
- 메모리 검색

### 명령줄

#### 녹화 시작

```bash
# 녹화 세션 시작
mnemosyne record --name "내 작업 세션"

# 녹화 중... 모든 행동이 캡처됩니다.
# Ctrl+C로 중지
```

#### AI로 분석

```bash
# 세션 분석 - AI가 각 행동의 의도 추론
mnemosyne analyze <session-id>

# 호기심 있는 AI가 행동에 대해 질문하게 하기
mnemosyne curious <session-id>
```

**호기심 출력 예시:**
```
🤔 세션에 대한 질문:

1. [높음] 왜 항상 이메일 확인 전에 Slack을 여나요?
   카테고리: 워크플로우 | 신뢰도: 0.89

2. [중간] "git status"를 23번 입력했는데 3번만 커밋했어요. 왜죠?
   카테고리: 습관 | 신뢰도: 0.72

3. [높음] 터미널로 전환하기 전 항상 2초 멈추네요.
   카테고리: 결정 | 신뢰도: 0.85
```

#### 메모리 작업

```bash
# 시맨틱으로 메모리 검색
mnemosyne memory "평소 아침을 어떻게 시작하는지"

# 최근 메모리 탐색
mnemosyne memory --recent

# 중요한 인사이트 찾기
mnemosyne memory --important
```

#### 목표 실행

```bash
# 학습된 행동 기반으로 목표 실행
mnemosyne execute "평소 코딩 환경 설정하기"

# 확인 모드와 함께 (더 안전)
mnemosyne execute "대기 중인 메시지에 답장하기" --confirm
```

---

## 🎮 CLI 레퍼런스

| 명령어 | 설명 |
|--------|------|
| `mnemosyne setup` | 대화형 설정 마법사 |
| `mnemosyne web` | **웹 인터페이스 시작** |
| `mnemosyne record` | 활동 기록 시작 |
| `mnemosyne sessions` | 기록된 세션 목록 |
| `mnemosyne analyze <id>` | AI가 세션 의도 분석 |
| `mnemosyne curious <id>` | AI가 행동에 대해 질문 |
| `mnemosyne memory [query]` | 메모리 검색 또는 탐색 |
| `mnemosyne export <id>` | 학습용 세션 내보내기 |
| `mnemosyne execute <goal>` | 목표 실행 |
| `mnemosyne status` | 현재 설정 표시 |
| `mnemosyne version` | 버전 표시 |

---

## ⚙️ 설정

설정은 `~/.mnemosyne/config.toml`에 저장됩니다:

```toml
[llm]
provider = "anthropic"  # openai, anthropic, google, ollama
model = "claude-3-opus-20240229"
api_key = "your-api-key"

[curiosity]
mode = "active"  # passive, active, proactive

[recording]
screenshot_quality = 80
screenshot_format = "webp"
mouse_throttle_ms = 50
```

---

## 🏗️ 프로젝트 구조

```
mnemosyne/
├── capture/      # 입력 기록 (마우스, 키보드, 화면)
├── store/        # SQLite 데이터베이스 및 세션 관리
├── reason/       # LLM 추론 및 호기심 질문
├── memory/       # 벡터 검색이 포함된 영구 메모리
├── learn/        # 학습 파이프라인 및 데이터셋
├── execute/      # 컴퓨터 제어 에이전트
├── llm/          # 멀티 프로바이더 LLM 추상화
├── config/       # 설정 및 구성
├── cli/          # 명령줄 인터페이스
└── web/          # 웹 인터페이스 (FastAPI + HTML/JS)
```

---

## 🔄 작동 원리

### 1. 캡처 단계
당신이 수행하는 모든 마이크로 액션이 기록됩니다:
- 마우스 위치, 클릭, 스크롤
- 키보드 입력 및 단축키
- 주요 순간의 스크린샷
- 활성 윈도우 컨텍스트

### 2. 추론 단계
호기심 있는 LLM이 당신의 행동을 분석합니다:
- **"왜 거기를 클릭했나요?"**
- **"타이핑에 어떤 패턴이 있나요?"**
- **"왜 앱 A에서 앱 B로 전환했나요?"**

### 3. 학습 단계
패턴이 추출되고 학습됩니다:
- 액션 시퀀스가 습관이 됩니다
- 의도가 예측 가능해집니다
- 당신의 "디지털 트윈"이 탄생합니다

### 4. 실행 단계
학습된 모델이 행동할 수 있습니다:
- 과거 행동을 기반으로 목표 실행
- 안전 장치가 위험한 행동 방지
- 민감한 작업에 대한 확인

---

## 🛡️ 안전 기능

Mnemosyne는 여러 안전 메커니즘을 포함합니다:

- **속도 제한**: 기본적으로 분당 최대 60개 액션
- **차단된 앱**: 터미널, 비밀번호 관리자, 시스템 환경설정
- **차단된 단축키**: Cmd+Q, Cmd+Shift+Q 등
- **안전 구역**: 특정 화면 영역으로 액션 제한
- **긴급 정지**: 모든 액션 즉시 중단

---

## 🤝 기여

기여를 환영합니다! PR을 제출하기 전에 기여 가이드라인을 읽어주세요.

---

## 📄 라이선스

MIT 라이선스 - 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

---

## 🙏 감사의 글

- 컴퓨터 제어 개념에 영감을 준 [OpenClaw](https://github.com/openclaw)
- 기록 패턴을 위한 [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt)
- 입력 모니터링을 위한 [pynput](https://github.com/moses-palmer/pynput)
