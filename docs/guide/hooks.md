# Hook System

Hook 시스템을 통해 Mnemosyne의 라이프사이클 이벤트에 반응하고 동작을 커스터마이징할 수 있습니다.

## 사용 가능한 Hook 이벤트

### 캡처 이벤트
| 이벤트 | 설명 |
|--------|------|
| `pre_capture` | 캡처 시작 전 |
| `post_capture` | 캡처 완료 후 |
| `capture_error` | 캡처 에러 발생 시 |

### 추론 이벤트
| 이벤트 | 설명 |
|--------|------|
| `pre_inference` | LLM 호출 전 |
| `post_inference` | LLM 응답 후 |
| `inference_error` | 추론 에러 시 |

### 실행 이벤트
| 이벤트 | 설명 |
|--------|------|
| `pre_execute` | 액션 실행 전 |
| `post_execute` | 액션 실행 후 |
| `execute_blocked` | 안전 장치 트리거 |

### 세션 이벤트
| 이벤트 | 설명 |
|--------|------|
| `session_start` | 세션 시작 |
| `session_end` | 세션 종료 |
| `session_pause` | 세션 일시정지 |
| `session_resume` | 세션 재개 |

### 메모리 이벤트
| 이벤트 | 설명 |
|--------|------|
| `pre_memory_store` | 메모리 저장 전 |
| `post_memory_store` | 메모리 저장 후 |
| `pre_memory_retrieve` | 메모리 검색 전 |
| `post_memory_retrieve` | 메모리 검색 후 |

## 기본 사용법

### 데코레이터로 등록

```python
from mnemosyne.hooks import HookEvent, HookPriority, hook

@hook(HookEvent.POST_CAPTURE)
async def log_capture(payload: dict) -> dict:
    print(f"캡처됨: {len(payload['events'])} 이벤트")
    return payload

@hook(HookEvent.PRE_EXECUTE, priority=HookPriority.HIGH)
async def validate_action(payload: dict) -> dict:
    if not is_safe(payload["action"]):
        payload["_cancel"] = True  # 이벤트 취소
    return payload
```

### HookManager 직접 사용

```python
from mnemosyne.hooks import HookManager, HookEvent

manager = HookManager()

# 핸들러 등록
async def my_handler(payload: dict) -> dict:
    payload["processed"] = True
    return payload

manager.register(HookEvent.POST_CAPTURE, my_handler, name="my_handler")

# 이벤트 트리거
result = await manager.trigger(HookEvent.POST_CAPTURE, {"events": events})
print(f"처리됨: {result.handlers_called}개 핸들러")

# 핸들러 비활성화/활성화
manager.disable("my_handler")
manager.enable("my_handler")

# 핸들러 제거
manager.unregister("my_handler")
```

### 여러 이벤트에 등록

```python
from mnemosyne.hooks import on_event, HookEvent

@on_event(HookEvent.SESSION_START, HookEvent.SESSION_END)
async def track_session(payload: dict) -> dict:
    print(f"세션 이벤트: {payload}")
    return payload
```

## 우선순위

핸들러는 우선순위 순서로 실행됩니다 (높은 것 먼저):

| 우선순위 | 값 | 용도 |
|---------|-----|------|
| `SYSTEM` | 200 | 내부 전용 |
| `HIGHEST` | 100 | 최우선 처리 |
| `HIGH` | 75 | 중요한 처리 |
| `NORMAL` | 50 | 기본값 |
| `LOW` | 25 | 후처리 |
| `LOWEST` | 0 | 마지막 처리 |

## 이벤트 취소

`pre_*` 이벤트는 취소할 수 있습니다:

```python
@hook(HookEvent.PRE_EXECUTE)
async def block_dangerous(payload: dict) -> dict:
    if is_dangerous(payload["action"]):
        payload["_cancel"] = True
        print("위험한 액션 차단됨!")
    return payload
```

## 통계 확인

```python
stats = manager.get_stats()
for name, info in stats.items():
    print(f"{name}: {info['call_count']}회 호출, 평균 {info['avg_time_ms']:.2f}ms")
```
