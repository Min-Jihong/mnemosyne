# Plugin System

Mnemosyne의 플러그인 시스템은 핵심 기능을 확장하고 커스터마이징할 수 있게 해줍니다.

## 개요

플러그인을 통해 다음을 할 수 있습니다:
- 라이프사이클 이벤트 후킹
- CLI 명령어 추가
- 웹 라우트 확장
- 새로운 LLM 프로바이더 추가
- 커스텀 캡처 소스 추가

## 플러그인 구조

```
my_plugin/
├── plugin.json       # 메타데이터 정의
├── __init__.py       # 플러그인 진입점
└── handlers.py       # 이벤트 핸들러 (선택)
```

## plugin.json 예시

```json
{
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "나의 플러그인",
    "entry_point": "__init__.py",
    "plugin_class": "MyPlugin",
    "hooks": ["post_capture", "pre_inference"],
    "dependencies": []
}
```

## 플러그인 작성하기

```python
from mnemosyne.plugins import MnemosynePlugin, PluginContext

class MyPlugin(MnemosynePlugin):
    async def on_load(self, context: PluginContext) -> None:
        """플러그인 로드 시 호출"""
        self.context = context
        context.log("플러그인 로드됨!")

    async def on_event(self, event_type: str, payload: dict) -> dict | None:
        """이벤트 발생 시 호출"""
        if event_type == "post_capture":
            # 캡처된 이벤트 처리
            payload["processed"] = True
            return payload
        return None

# 필수: 플러그인 클래스 내보내기
Plugin = MyPlugin
```

## 플러그인 설치

플러그인을 `~/.mnemosyne/plugins/` 디렉토리에 복사합니다:

```bash
mkdir -p ~/.mnemosyne/plugins/my-plugin
cp -r my_plugin/* ~/.mnemosyne/plugins/my-plugin/
```

## 프로그래밍 방식 사용

```python
from mnemosyne.plugins import PluginManager, initialize_plugins

# 모든 플러그인 초기화
results = await initialize_plugins()

# 또는 수동으로
manager = PluginManager()
await manager.discover_plugins()
await manager.load_all_plugins()

# 특정 플러그인 로드
plugin = await manager.load_plugin("my-plugin")

# 플러그인 비활성화
await manager.disable_plugin("my-plugin")

# 이벤트 발송
result = await manager.dispatch_event("post_capture", {"events": events})
```

## 빌트인 플러그인

Mnemosyne에는 예제 플러그인이 포함되어 있습니다:

```
mnemosyne/plugins/builtin/example/
├── plugin.json
└── __init__.py
```

이 예제를 참고하여 자신만의 플러그인을 만들어보세요.
