# Terminal UI (TUI)

Textual 기반의 전문적인 터미널 인터페이스로 Mnemosyne를 사용할 수 있습니다.

## 설치

```bash
pip install "mnemosyne[tui]"
```

## 실행

```bash
mnemosyne tui
```

## 화면 구성

TUI는 4개의 탭으로 구성됩니다:

### Events 탭
- 실시간 이벤트 로그 표시
- 마우스, 키보드, 윈도우 이벤트를 색상으로 구분
- 타임스탬프와 함께 표시

### Sessions 탭
- 녹화된 세션 목록
- ID, 이름, 날짜, 이벤트 수, 시간 표시
- 세션 선택 및 상세 보기

### Memory 탭
- 시맨틱 메모리 검색
- 검색어 입력으로 관련 기억 찾기
- 검색 결과 하이라이트

### Chat 탭
- 디지털 트윈과 채팅
- 자연어로 질문하기
- 실시간 응답 표시

## 키보드 단축키

| 키 | 동작 |
|----|------|
| `r` | 녹화 시작/중지 |
| `e` | Events 탭으로 이동 |
| `s` | Sessions 탭으로 이동 |
| `m` | Memory 탭으로 이동 |
| `c` | Chat 탭으로 이동 |
| `?` | 도움말 표시 |
| `q` | 종료 |
| `Esc` | 취소 |

## 상태 바

화면 상단의 상태 바에서:
- 🔴 녹화 중일 때 빨간색 표시
- 현재 세션 이름
- 캡처된 이벤트 수

## 스크린샷

```
┌─────────────────────────────────────────────────────────────┐
│ 🧠 Mnemosyne - Your Digital Twin                            │
├─────────────────────────────────────────────────────────────┤
│ ● RECORDING | Session: Work_Session | Events: 1,234        │
├─────────────────────────────────────────────────────────────┤
│ [Events] [Sessions] [Memory] [Chat]                         │
│                                                             │
│ 14:32:01 mouse_click                                        │
│ 14:32:02 key_press                                          │
│ 14:32:03 window_change                                      │
│ 14:32:05 mouse_scroll                                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ r:Record  e:Events  s:Sessions  m:Memory  c:Chat  q:Quit    │
└─────────────────────────────────────────────────────────────┘
```

## 프로그래밍 방식 사용

```python
from mnemosyne.tui import MnemosyneApp

app = MnemosyneApp()
app.run()
```

## 요구 사항

- Python 3.11+
- Textual 0.47+
- 터미널: 256색 지원 권장
