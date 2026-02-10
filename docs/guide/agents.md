# Agent Orchestration

여러 특화된 AI 에이전트를 조율하여 복잡한 작업을 수행할 수 있습니다.

## 에이전트 유형

| 에이전트 | 역할 |
|---------|------|
| `OBSERVER` | 사용자 행동 관찰 및 기록 |
| `ANALYZER` | 패턴 분석 및 인사이트 생성 |
| `EXECUTOR` | 학습된 행동 기반 액션 실행 |
| `PLANNER` | 다단계 작업 계획 수립 |
| `LIBRARIAN` | 메모리 검색 및 정보 검색 |
| `CURIOUS` | 사용자 의도 파악을 위한 질문 생성 |

## 기본 사용법

```python
from mnemosyne.agents import AgentOrchestrator, AgentType
from mnemosyne.llm.factory import create_llm_provider
from mnemosyne.memory.persistent import PersistentMemory

# 오케스트레이터 생성
llm = create_llm_provider(settings.llm)
memory = PersistentMemory()
orchestrator = AgentOrchestrator(llm=llm, memory=memory)

# 단일 에이전트 실행
result = await orchestrator.run(
    AgentType.ANALYZER,
    "왜 나는 항상 아침에 Slack을 먼저 확인할까?"
)
print(result.output)
```

## 병렬 실행

여러 에이전트를 동시에 실행:

```python
results = await orchestrator.run_parallel([
    (AgentType.ANALYZER, "내 아침 루틴을 분석해줘"),
    (AgentType.LIBRARIAN, "비슷한 패턴을 찾아줘"),
    (AgentType.CURIOUS, "더 알아야 할 것들을 질문해줘"),
])

for result in results:
    print(f"{result.agent_type.value}: {result.output[:100]}...")
```

## 파이프라인 실행

에이전트를 순차적으로 실행하고 결과를 전달:

```python
results = await orchestrator.run_pipeline([
    (AgentType.LIBRARIAN, "프로젝트 관련 기억을 찾아줘"),
    (AgentType.ANALYZER, "찾은 정보를 분석해줘"),
    (AgentType.PLANNER, "분석 결과로 계획을 세워줘"),
])

# 마지막 결과에 모든 정보가 누적됨
final_plan = results[-1]
print(final_plan.data.get("steps", []))
```

## 빌트인 워크플로우

### 분석 및 계획

```python
# 자동으로 분석 → 검색 → 계획 수행
result = await orchestrator.analyze_and_plan(
    "내 코딩 생산성을 높이고 싶어"
)

print(f"분석: {result['analysis']}")
print(f"관련 기억: {result['memories']}개")
print(f"계획: {result['steps']}")
```

## 컨텍스트 공유

에이전트 간 컨텍스트 공유:

```python
from mnemosyne.agents import AgentContext

context = AgentContext(
    session_id="current_session",
    user_query="내 습관을 개선하고 싶어",
    metadata={"priority": "high"}
)

# 모든 에이전트가 동일한 컨텍스트 사용
results = await orchestrator.run_parallel([
    (AgentType.ANALYZER, "현재 습관 분석"),
    (AgentType.PLANNER, "개선 계획 수립"),
], context=context)
```

## 실행 이력

```python
# 최근 실행 이력 조회
history = orchestrator.get_history(limit=10)
for result in history:
    print(f"{result.agent_type.value}: {result.status.value}")

# 통계 확인
stats = orchestrator.stats()
print(f"총 실행: {stats['total_executions']}")
print(f"성공률: {stats['success_rate']:.1%}")
print(f"토큰 사용: {stats['total_tokens']}")

# 이력 초기화
orchestrator.clear_history()
```

## 커스텀 에이전트 추가

```python
from mnemosyne.agents.base import BaseAgent, AGENT_CLASSES
from mnemosyne.agents.types import AgentType, AgentResult, AgentStatus

class MyCustomAgent(BaseAgent):
    agent_type = AgentType.ANALYZER  # 또는 새 타입 추가

    async def execute(self, query: str, context: AgentContext) -> AgentResult:
        # 커스텀 로직
        output, tokens = await self._call_llm(f"커스텀 분석: {query}")
        return self._create_result(
            status=AgentStatus.COMPLETED,
            output=output,
            tokens=tokens,
        )

# 등록
AGENT_CLASSES[AgentType.ANALYZER] = MyCustomAgent
```
