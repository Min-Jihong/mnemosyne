# Background Tasks

백그라운드 태스크 시스템으로 비동기 작업을 병렬로 실행할 수 있습니다.

## 기본 사용법

### 태스크 등록 및 실행

```python
from mnemosyne.tasks import TaskManager, TaskPriority

manager = TaskManager(max_workers=5)

# 데코레이터로 등록
@manager.task(priority=TaskPriority.HIGH)
async def analyze_session(session_id: str) -> dict:
    # 무거운 분석 작업
    result = await heavy_analysis(session_id)
    return result

# 매니저 시작
await manager.start()

# 태스크 제출
task_id = await manager.submit("analyze_session", session_id="abc123")
print(f"태스크 시작: {task_id}")

# 결과 대기
result = await manager.get_result(task_id, timeout=60.0)
print(f"결과: {result.result}")

# 매니저 종료
await manager.stop()
```

### 일회성 태스크

```python
async def custom_task(x: int, y: int) -> int:
    return x + y

task_id = await manager.submit_raw(custom_task, 10, 20, name="add")
result = await manager.get_result(task_id)
print(result.result)  # 30
```

## 우선순위

태스크는 우선순위 순서로 실행됩니다:

| 우선순위 | 값 | 용도 |
|---------|-----|------|
| `CRITICAL` | 100 | 긴급 작업 |
| `HIGH` | 75 | 중요 작업 |
| `NORMAL` | 50 | 기본값 |
| `LOW` | 10 | 백그라운드 작업 |

```python
# 높은 우선순위로 제출
task_id = await manager.submit("my_task", priority=TaskPriority.CRITICAL)
```

## 진행 상황 추적

```python
# 태스크 상태 확인
status = manager.get_status(task_id)
print(f"상태: {status}")  # TaskStatus.RUNNING

# 진행률 확인
progress, message = manager.get_progress(task_id)
print(f"진행: {progress * 100:.0f}% - {message}")

# 태스크 내에서 진행률 업데이트
@manager.task()
async def long_task():
    task = manager.get_task(current_task_id)
    for i in range(100):
        task.update_progress(i / 100, f"처리 중... {i}/100")
        await process_item(i)
```

## 취소

```python
# 태스크 취소
cancelled = await manager.cancel(task_id)
if cancelled:
    print("태스크가 취소되었습니다")
```

## 재시도

실패한 태스크는 자동으로 재시도됩니다:

```python
@manager.task(max_retries=3)
async def flaky_task():
    # 실패하면 최대 3번 재시도
    result = await unreliable_api_call()
    return result
```

## 타임아웃

```python
@manager.task(timeout=30.0)  # 30초 타임아웃
async def slow_task():
    await very_slow_operation()
```

## 통계

```python
stats = manager.stats()
print(f"총 태스크: {stats['total_tasks']}")
print(f"대기 중: {stats['queued']}")
print(f"실행 중: {stats['running']}")
print(f"상태별: {stats['by_status']}")
```

## 태스크 목록

```python
# 모든 태스크
all_tasks = manager.list_tasks()

# 상태별 필터
running = manager.list_tasks(status=TaskStatus.RUNNING)
completed = manager.list_tasks(status=TaskStatus.COMPLETED)
```

## 전역 매니저

```python
from mnemosyne.tasks import get_task_manager

# 전역 매니저 사용
manager = get_task_manager()
await manager.start()
```
