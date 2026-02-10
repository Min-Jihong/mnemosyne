# WebSocket Gateway

실시간 양방향 통신을 위한 WebSocket 게이트웨이 프로토콜입니다.

## 개요

Gateway는 다음 기능을 제공합니다:
- 다중 클라이언트 지원
- 이벤트 스트리밍 (시퀀스 번호 포함)
- 프레즌스 트래킹
- 하트비트 모니터링
- 갭 감지 및 복구

## 서버 측 사용

### FastAPI와 통합

```python
from fastapi import FastAPI, WebSocket
from mnemosyne.web.gateway import Gateway, GatewayEventType

app = FastAPI()
gateway = Gateway()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client = await gateway.connect(websocket)
    
    try:
        while True:
            message = await websocket.receive_text()
            response = await gateway.handle_message(client.client_id, message)
            if response:
                await websocket.send_text(response.model_dump_json())
    except:
        await gateway.disconnect(client.client_id)

# 애플리케이션 시작 시
@app.on_event("startup")
async def startup():
    await gateway.start_heartbeat_monitor()

@app.on_event("shutdown")
async def shutdown():
    await gateway.stop_heartbeat_monitor()
```

### 이벤트 핸들러 등록

```python
@gateway.on_event(GatewayEventType.CHAT_MESSAGE)
async def handle_chat(client, event):
    # 채팅 메시지 처리
    response = await process_chat(event.payload["text"])
    return GatewayEvent(
        type=GatewayEventType.CHAT_MESSAGE,
        payload={"text": response}
    )
```

### 이벤트 브로드캐스트

```python
# 모든 클라이언트에게 전송
await gateway.broadcast(
    GatewayEventType.RECORDING_EVENT,
    {"event": "mouse_click", "x": 100, "y": 200}
)

# 특정 클라이언트 제외
await gateway.broadcast(
    GatewayEventType.PRESENCE_UPDATE,
    {"user": "john", "status": "away"},
    exclude=["client-123"]
)

# 특정 클라이언트에게만
await gateway.send(
    "client-456",
    GatewayEventType.SYSTEM,
    {"message": "Welcome!"}
)
```

## 클라이언트 측 사용 (JavaScript)

```javascript
class MnemosyneClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.lastSeq = 0;
    }

    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleEvent(data);
        };
        
        this.ws.onopen = () => {
            // 인증
            this.send({
                type: "identify",
                payload: {
                    user_id: "user-123",
                    device_type: "web"
                }
            });
        };
    }

    handleEvent(event) {
        // 시퀀스 번호 체크 (갭 감지)
        if (event.seq && event.seq > this.lastSeq + 1) {
            console.warn("Gap detected:", this.lastSeq, "->", event.seq);
            this.requestMissingEvents(this.lastSeq);
        }
        this.lastSeq = event.seq || this.lastSeq;

        switch (event.type) {
            case "ready":
                console.log("Connected! Presence:", event.payload.presence);
                break;
            case "chat.message":
                this.onChatMessage(event.payload);
                break;
            case "recording.event":
                this.onRecordingEvent(event.payload);
                break;
        }
    }

    send(event) {
        this.ws.send(JSON.stringify(event));
    }

    // 하트비트
    startHeartbeat(interval) {
        setInterval(() => {
            this.send({ type: "heartbeat", payload: {} });
        }, interval);
    }
}

// 사용
const client = new MnemosyneClient("ws://localhost:8000/ws");
client.connect();
```

## 이벤트 타입

### 연결 이벤트
| 타입 | 설명 |
|------|------|
| `hello` | 연결 시 서버에서 전송 |
| `identify` | 클라이언트 인증 |
| `ready` | 인증 완료 |
| `heartbeat` | 연결 유지 |
| `heartbeat_ack` | 하트비트 응답 |

### 애플리케이션 이벤트
| 타입 | 설명 |
|------|------|
| `chat.message` | 채팅 메시지 |
| `chat.stream_start` | 스트리밍 시작 |
| `chat.stream_chunk` | 스트리밍 청크 |
| `chat.stream_end` | 스트리밍 종료 |
| `recording.start` | 녹화 시작 |
| `recording.stop` | 녹화 중지 |
| `recording.event` | 녹화 이벤트 |

### 프레즌스 이벤트
| 타입 | 설명 |
|------|------|
| `presence.join` | 사용자 접속 |
| `presence.leave` | 사용자 퇴장 |
| `presence.update` | 상태 변경 |

## 프레즌스 조회

```python
# 현재 연결된 모든 클라이언트
presence = gateway.get_presence()
for client in presence:
    print(f"{client['user_id']}: {client['state']}")
```

## 갭 복구

```python
# 놓친 이벤트 조회
missed_events = await gateway.get_events_since(last_seq=100)
for event in missed_events:
    process_event(event)
```
