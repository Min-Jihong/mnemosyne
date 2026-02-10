"""
Mnemosyne Web Application

FastAPI-based web server for the Mnemosyne digital twin system.
Provides chat interface, recording control, memory queries, and settings management.
"""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from mnemosyne.web.chat import ChatHandler
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.config.schema import LLMProvider


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class SettingsUpdate(BaseModel):
    provider: str
    api_key: str
    model: str | None = None


class SettingsResponse(BaseModel):
    provider: str | None
    model: str | None
    configured: bool


class MemoryQuery(BaseModel):
    query: str
    n_results: int = 10


class MemoryItem(BaseModel):
    id: str
    content: str
    type: str
    importance: float
    timestamp: str


class RecordingStatus(BaseModel):
    is_recording: bool
    session_id: str | None
    session_name: str | None
    event_count: int


class StartRecordingRequest(BaseModel):
    name: str | None = None


# ============================================================================
# Application State
# ============================================================================

class AppState:
    def __init__(self):
        self.data_dir = Path.home() / ".mnemosyne"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.chat_handler = ChatHandler(data_dir=self.data_dir)
        self.memory: PersistentMemory | None = None
        self.recording_session: dict[str, Any] | None = None
        self.websocket_connections: list[WebSocket] = []
    
    def init_memory(self):
        if self.memory is None:
            try:
                self.memory = PersistentMemory(data_dir=self.data_dir)
                self.chat_handler.memory = self.memory
            except Exception:
                pass  # Memory init can fail if dependencies missing
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients."""
        for ws in self.websocket_connections[:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.websocket_connections.remove(ws)


app_state = AppState()


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    app_state.init_memory()
    yield
    # Shutdown
    pass


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Mnemosyne",
    description="Your Digital Twin - Learn to think like you",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = None
if TEMPLATES_DIR.exists() and (TEMPLATES_DIR / "index.html").exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================================
# Web UI Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web UI."""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    
    # Fallback: serve embedded HTML if no template
    return HTMLResponse(content=get_embedded_html(), status_code=200)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "mnemosyne"}


# ============================================================================
# Chat API
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Send a message to the AI and get a response."""
    conversation_id = message.conversation_id or str(uuid.uuid4())
    
    response = await app_state.chat_handler.chat(
        message=message.message,
        conversation_id=conversation_id,
    )
    
    return ChatResponse(response=response, conversation_id=conversation_id)


@app.get("/api/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat history for a conversation."""
    history = app_state.chat_handler.get_conversation_history(conversation_id)
    return {"conversation_id": conversation_id, "messages": history}


@app.delete("/api/chat/history/{conversation_id}")
async def clear_chat_history(conversation_id: str):
    """Clear chat history for a conversation."""
    app_state.chat_handler.clear_conversation(conversation_id)
    return {"status": "cleared", "conversation_id": conversation_id}


# ============================================================================
# WebSocket for Real-time Chat
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    app_state.websocket_connections.append(websocket)
    
    conversation_id = str(uuid.uuid4())
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            conv_id = data.get("conversation_id", conversation_id)
            
            # Send typing indicator
            await websocket.send_json({"type": "typing", "status": True})
            
            # Get response
            response = await app_state.chat_handler.chat(
                message=message,
                conversation_id=conv_id,
            )
            
            # Send response
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": response,
                "conversation_id": conv_id,
            })
            
    except WebSocketDisconnect:
        app_state.websocket_connections.remove(websocket)


# ============================================================================
# Settings API
# ============================================================================

@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current LLM settings."""
    config = app_state.chat_handler._llm_config
    
    if config:
        return SettingsResponse(
            provider=config.provider.value,
            model=config.model,
            configured=True,
        )
    
    return SettingsResponse(provider=None, model=None, configured=False)


@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update LLM settings with API key."""
    try:
        app_state.chat_handler.set_api_key(
            provider=settings.provider,
            api_key=settings.api_key,
            model=settings.model,
        )
        return {"status": "success", "message": "Settings updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/settings/providers")
async def get_providers():
    """Get available LLM providers."""
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"],
                "default_model": "gpt-4o",
            },
            {
                "id": "anthropic", 
                "name": "Anthropic",
                "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
                "default_model": "claude-sonnet-4-20250514",
            },
            {
                "id": "google",
                "name": "Google",
                "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash"],
                "default_model": "gemini-2.0-flash",
            },
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "models": ["llama3.2", "llama3.1", "mistral", "gemma3", "deepseek-r1", "qwen2.5", "codellama"],
                "default_model": "llama3.2",
                "requires_api_key": False,
            },
        ]
    }


@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get installed Ollama models."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"].split(":")[0] for m in data.get("models", [])]
                return {"models": models, "running": True}
    except Exception:
        pass
    return {"models": [], "running": False}


# ============================================================================
# Memory API
# ============================================================================

@app.post("/api/memory/search")
async def search_memory(query: MemoryQuery):
    """Search memories semantically."""
    if not app_state.memory:
        return {"memories": [], "message": "Memory system not initialized"}
    
    memories = app_state.memory.recall(query=query.query, n_results=query.n_results)
    
    return {
        "memories": [
            {
                "id": str(m.id),
                "content": m.content,
                "type": m.type.value,
                "importance": m.importance,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in memories
        ]
    }


@app.get("/api/memory/recent")
async def get_recent_memories(limit: int = 20):
    """Get recent memories."""
    if not app_state.memory:
        return {"memories": [], "message": "Memory system not initialized"}
    
    memories = app_state.memory.get_recent(limit=limit)
    
    return {
        "memories": [
            {
                "id": str(m.id),
                "content": m.content,
                "type": m.type.value,
                "importance": m.importance,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in memories
        ]
    }


@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    if not app_state.memory:
        return {"count": 0, "initialized": False}
    
    return {
        "count": app_state.memory.count(),
        "initialized": True,
    }


# ============================================================================
# Recording API
# ============================================================================

@app.get("/api/recording/status", response_model=RecordingStatus)
async def get_recording_status():
    """Get current recording status."""
    if app_state.recording_session:
        return RecordingStatus(
            is_recording=True,
            session_id=app_state.recording_session.get("id"),
            session_name=app_state.recording_session.get("name"),
            event_count=app_state.recording_session.get("event_count", 0),
        )
    
    return RecordingStatus(
        is_recording=False,
        session_id=None,
        session_name=None,
        event_count=0,
    )


@app.post("/api/recording/start")
async def start_recording(request: StartRecordingRequest):
    """Start a new recording session."""
    if app_state.recording_session:
        raise HTTPException(status_code=400, detail="Recording already in progress")
    
    session_id = str(uuid.uuid4())[:8]
    session_name = request.name or f"Session {session_id}"
    
    app_state.recording_session = {
        "id": session_id,
        "name": session_name,
        "event_count": 0,
    }
    
    # Broadcast to WebSocket clients
    await app_state.broadcast({
        "type": "recording_started",
        "session_id": session_id,
        "session_name": session_name,
    })
    
    return {"status": "started", "session_id": session_id, "session_name": session_name}


@app.post("/api/recording/stop")
async def stop_recording():
    """Stop the current recording session."""
    if not app_state.recording_session:
        raise HTTPException(status_code=400, detail="No recording in progress")
    
    session = app_state.recording_session
    app_state.recording_session = None
    
    # Broadcast to WebSocket clients
    await app_state.broadcast({
        "type": "recording_stopped",
        "session_id": session["id"],
        "event_count": session["event_count"],
    })
    
    return {
        "status": "stopped",
        "session_id": session["id"],
        "event_count": session["event_count"],
    }


# ============================================================================
# Sessions API
# ============================================================================

@app.get("/api/sessions")
async def list_sessions():
    """List all recorded sessions."""
    # TODO: Integrate with actual session storage
    sessions_dir = app_state.data_dir / "sessions"
    
    if not sessions_dir.exists():
        return {"sessions": []}
    
    sessions = []
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file) as f:
                data = json.load(f)
                sessions.append({
                    "id": data.get("id", session_file.stem),
                    "name": data.get("name", "Unnamed"),
                    "created_at": data.get("created_at"),
                    "event_count": data.get("event_count", 0),
                })
        except Exception:
            continue
    
    return {"sessions": sessions}


# ============================================================================
# Embedded HTML (Fallback when no template exists)
# ============================================================================

def get_embedded_html() -> str:
    """Return embedded HTML for the web UI."""
    return r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mnemosyne - Your Digital Twin</title>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --text-primary: #e4e4e7;
            --text-secondary: #a1a1aa;
            --accent: #8b5cf6;
            --accent-hover: #7c3aed;
            --border: #27272a;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header */
        header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .logo-icon {
            font-size: 1.5rem;
        }
        
        .logo-text {
            font-size: 1.25rem;
            font-weight: 600;
            background: linear-gradient(135deg, var(--accent), #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-actions {
            display: flex;
            gap: 1rem;
        }
        
        .nav-btn {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
        }
        
        .nav-btn:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .nav-btn.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        /* Main Layout */
        main {
            flex: 1;
            display: flex;
            max-height: calc(100vh - 60px);
        }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-section {
            padding: 1rem;
            border-bottom: 1px solid var(--border);
        }
        
        .sidebar-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            letter-spacing: 0.05em;
        }
        
        .status-card {
            background: var(--bg-tertiary);
            border-radius: 0.5rem;
            padding: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--error);
        }
        
        .status-indicator.active {
            background: var(--success);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .status-text {
            font-size: 0.875rem;
        }
        
        .conversation-list {
            flex: 1;
            overflow-y: auto;
            padding: 0.5rem;
        }
        
        .conversation-item {
            padding: 0.75rem;
            border-radius: 0.5rem;
            cursor: pointer;
            margin-bottom: 0.25rem;
            transition: background 0.2s;
        }
        
        .conversation-item:hover {
            background: var(--bg-tertiary);
        }
        
        .conversation-item.active {
            background: var(--accent);
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2));
            border: 1px solid var(--accent);
        }
        
        .new-chat-btn {
            margin: 1rem;
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.2s;
        }
        
        .new-chat-btn:hover {
            background: var(--accent-hover);
        }
        
        /* Chat Area */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .message {
            display: flex;
            gap: 1rem;
            max-width: 800px;
        }
        
        .message.user {
            flex-direction: row-reverse;
            align-self: flex-end;
        }
        
        .message-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 1rem;
        }
        
        .message.user .message-avatar {
            background: var(--accent);
        }
        
        .message-content {
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 1rem;
            line-height: 1.6;
        }
        
        .message.user .message-content {
            background: var(--accent);
            color: white;
        }
        
        .message-content p {
            margin-bottom: 0.5rem;
        }
        
        .message-content p:last-child {
            margin-bottom: 0;
        }
        
        .message-content code {
            background: rgba(0, 0, 0, 0.3);
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.875em;
        }
        
        .message-content pre {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        
        .message-content pre code {
            background: none;
            padding: 0;
        }
        
        /* Welcome Screen */
        .welcome {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            text-align: center;
        }
        
        .welcome-icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
        }
        
        .welcome h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--accent), #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .welcome p {
            color: var(--text-secondary);
            max-width: 400px;
            line-height: 1.6;
        }
        
        .welcome-features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 2rem;
            max-width: 500px;
        }
        
        .feature-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            text-align: left;
        }
        
        .feature-card h3 {
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }
        
        .feature-card p {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        /* Chat Input */
        .chat-input-container {
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--border);
            background: var(--bg-secondary);
        }
        
        .chat-input-wrapper {
            max-width: 800px;
            margin: 0 auto;
            position: relative;
        }
        
        .chat-input {
            width: 100%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1rem 3rem 1rem 1rem;
            color: var(--text-primary);
            font-size: 1rem;
            resize: none;
            outline: none;
            transition: border-color 0.2s;
        }
        
        .chat-input:focus {
            border-color: var(--accent);
        }
        
        .chat-input::placeholder {
            color: var(--text-secondary);
        }
        
        .send-btn {
            position: absolute;
            right: 0.5rem;
            bottom: 0.5rem;
            background: var(--accent);
            border: none;
            color: white;
            width: 36px;
            height: 36px;
            border-radius: 0.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        .send-btn:hover {
            background: var(--accent-hover);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Settings Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .modal-overlay.show {
            display: flex;
        }
        
        .modal {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 2rem;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal h2 {
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .form-group {
            margin-bottom: 1.25rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .form-group select,
        .form-group input {
            width: 100%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 0.75rem;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .form-group select:focus,
        .form-group input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .modal-actions {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .btn {
            flex: 1;
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: var(--accent);
            border: none;
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--accent-hover);
        }
        
        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-primary);
        }
        
        .btn-secondary:hover {
            background: var(--bg-tertiary);
        }
        
        /* Typing indicator */
        .typing-indicator {
            display: flex;
            gap: 0.25rem;
            padding: 0.5rem;
        }
        
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: var(--text-secondary);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 100% { opacity: 0.3; transform: translateY(0); }
            50% { opacity: 1; transform: translateY(-4px); }
        }
        
        /* Toast notifications */
        .toast-container {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 1001;
        }
        
        .toast {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem 1.5rem;
            margin-top: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            animation: slideIn 0.3s ease;
        }
        
        .toast.success { border-color: var(--success); }
        .toast.error { border-color: var(--error); }
        .toast.warning { border-color: var(--warning); }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            
            .chat-messages {
                padding: 1rem;
            }
            
            .welcome-features {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <span class="logo-icon">🧠</span>
            <span class="logo-text">Mnemosyne</span>
        </div>
        <div class="nav-actions">
            <button class="nav-btn" onclick="showSettings()">⚙️ Settings</button>
            <button class="nav-btn" id="recordBtn" onclick="toggleRecording()">🔴 Record</button>
        </div>
    </header>
    
    <main>
        <aside class="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">Status</div>
                <div class="status-card">
                    <div class="status-indicator" id="llmStatus"></div>
                    <span class="status-text" id="llmStatusText">LLM Not Configured</span>
                </div>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Conversations</div>
            </div>
            
            <div class="conversation-list" id="conversationList">
                <!-- Conversations will be listed here -->
            </div>
            
            <button class="new-chat-btn" onclick="newChat()">+ New Chat</button>
        </aside>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="welcome">
                    <div class="welcome-icon">🧠</div>
                    <h1>Your Digital Twin Awaits</h1>
                    <p>I learn to think like you by observing your actions and understanding your patterns. Start a conversation or begin recording.</p>
                    
                    <div class="welcome-features">
                        <div class="feature-card">
                            <h3>🎯 Record & Learn</h3>
                            <p>Capture your computer interactions</p>
                        </div>
                        <div class="feature-card">
                            <h3>🤔 Ask & Understand</h3>
                            <p>I ask why you do what you do</p>
                        </div>
                        <div class="feature-card">
                            <h3>🧠 Remember Forever</h3>
                            <p>Persistent memory of our chats</p>
                        </div>
                        <div class="feature-card">
                            <h3>⚡ Act Like You</h3>
                            <p>Execute tasks your way</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <div class="chat-input-wrapper">
                    <textarea 
                        class="chat-input" 
                        id="chatInput" 
                        placeholder="Talk to your digital twin..."
                        rows="1"
                        onkeydown="handleKeyDown(event)"
                    ></textarea>
                    <button class="send-btn" onclick="sendMessage()" id="sendBtn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </main>
    
    <!-- Settings Modal -->
    <div class="modal-overlay" id="settingsModal">
        <div class="modal">
            <h2>⚙️ Settings</h2>
            
            <div class="form-group">
                <label>LLM Provider</label>
                <select id="providerSelect" onchange="updateProviderUI()">
                    <option value="openai">OpenAI (GPT-4o)</option>
                    <option value="anthropic">Anthropic (Claude Sonnet 4)</option>
                    <option value="google">Google (Gemini 2.0)</option>
                    <option value="ollama">Ollama (Local - No API Key)</option>
                </select>
            </div>
            
            <div class="form-group" id="apiKeyGroup">
                <label>API Key</label>
                <input type="password" id="apiKeyInput" placeholder="Enter your API key">
                <small style="color: var(--text-secondary); font-size: 0.75rem; margin-top: 0.25rem; display: block;">
                    Model is auto-selected. Change via chat: "use gpt-4o-mini"
                </small>
            </div>
            
            <div class="form-group" id="ollamaInfo" style="display: none;">
                <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 0.5rem; font-size: 0.875rem;">
                    <strong>Ollama detected!</strong><br>
                    <span id="ollamaModelInfo">Checking installed models...</span>
                </div>
            </div>
            
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="hideSettings()">Cancel</button>
                <button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        // State
        let conversationId = null;
        let isRecording = false;
        let providers = {};
        
        // Initialize
        document.addEventListener('DOMContentLoaded', async () => {
            await checkSettings();
            await loadProviders();
            autoResizeInput();
        });
        
        // Auto-resize textarea
        function autoResizeInput() {
            const input = document.getElementById('chatInput');
            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 200) + 'px';
            });
        }
        
        // Check LLM settings
        async function checkSettings() {
            try {
                const res = await fetch('/api/settings');
                const data = await res.json();
                
                const indicator = document.getElementById('llmStatus');
                const text = document.getElementById('llmStatusText');
                
                if (data.configured) {
                    indicator.classList.add('active');
                    text.textContent = `${data.provider} (${data.model})`;
                } else {
                    indicator.classList.remove('active');
                    text.textContent = 'LLM Not Configured';
                }
            } catch (e) {
                console.error('Failed to check settings:', e);
            }
        }
        
        // Load providers
        async function loadProviders() {
            try {
                const res = await fetch('/api/settings/providers');
                const data = await res.json();
                providers = {};
                data.providers.forEach(p => providers[p.id] = p);
                updateProviderUI();
            } catch (e) {
                console.error('Failed to load providers:', e);
            }
        }
        
        // Update UI based on provider selection
        function updateProviderUI() {
            const provider = document.getElementById('providerSelect').value;
            const apiKeyGroup = document.getElementById('apiKeyGroup');
            const ollamaInfo = document.getElementById('ollamaInfo');
            
            const p = providers[provider];
            if (p) {
                if (p.requires_api_key === false) {
                    apiKeyGroup.style.display = 'none';
                    ollamaInfo.style.display = 'block';
                    checkOllamaModels();
                } else {
                    apiKeyGroup.style.display = 'block';
                    ollamaInfo.style.display = 'none';
                }
            }
        }
        
        // Check Ollama installed models
        async function checkOllamaModels() {
            const infoEl = document.getElementById('ollamaModelInfo');
            try {
                const res = await fetch('/api/ollama/models');
                const data = await res.json();
                if (data.models && data.models.length > 0) {
                    infoEl.innerHTML = `Will use: <strong>${data.models[0]}</strong><br>` +
                        `Installed: ${data.models.join(', ')}`;
                } else {
                    infoEl.innerHTML = 'No models found. Run: <code>ollama pull llama3.2</code>';
                }
            } catch (e) {
                infoEl.innerHTML = 'Ollama not running. Start it first.';
            }
        }
        
        // Settings modal
        function showSettings() {
            document.getElementById('settingsModal').classList.add('show');
        }
        
        function hideSettings() {
            document.getElementById('settingsModal').classList.remove('show');
        }
        
        async function saveSettings() {
            const provider = document.getElementById('providerSelect').value;
            const apiKey = document.getElementById('apiKeyInput').value;
            
            if (providers[provider]?.requires_api_key !== false && !apiKey) {
                showToast('Please enter an API key', 'error');
                return;
            }
            
            try {
                const res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider, api_key: apiKey })
                });
                
                if (res.ok) {
                    showToast('Settings saved successfully', 'success');
                    hideSettings();
                    await checkSettings();
                } else {
                    const data = await res.json();
                    showToast(data.detail || 'Failed to save settings', 'error');
                }
            } catch (e) {
                showToast('Failed to save settings', 'error');
            }
        }
        
        // Chat functions
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Clear input
            input.value = '';
            input.style.height = 'auto';
            
            // Remove welcome screen
            const welcome = document.querySelector('.welcome');
            if (welcome) welcome.remove();
            
            // Add user message
            addMessage('user', message);
            
            // Show typing indicator
            const typingId = showTyping();
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message, 
                        conversation_id: conversationId 
                    })
                });
                
                const data = await res.json();
                conversationId = data.conversation_id;
                
                // Remove typing indicator and add response
                removeTyping(typingId);
                addMessage('assistant', data.response);
                
            } catch (e) {
                removeTyping(typingId);
                addMessage('assistant', 'Sorry, I encountered an error. Please check your settings.');
            }
        }
        
        function addMessage(role, content) {
            const container = document.getElementById('chatMessages');
            const avatar = role === 'user' ? '👤' : '🧠';
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${formatContent(content)}</div>
            `;
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function formatContent(content) {
            // Simple markdown-like formatting
            return content
                .replace(/\n/g, '<br>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        }
        
        function showTyping() {
            const container = document.getElementById('chatMessages');
            const id = 'typing-' + Date.now();
            
            const typingDiv = document.createElement('div');
            typingDiv.id = id;
            typingDiv.className = 'message';
            typingDiv.innerHTML = `
                <div class="message-avatar">🧠</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;
            
            container.appendChild(typingDiv);
            container.scrollTop = container.scrollHeight;
            
            return id;
        }
        
        function removeTyping(id) {
            const typing = document.getElementById(id);
            if (typing) typing.remove();
        }
        
        // New chat
        function newChat() {
            conversationId = null;
            document.getElementById('chatMessages').innerHTML = `
                <div class="welcome">
                    <div class="welcome-icon">🧠</div>
                    <h1>Your Digital Twin Awaits</h1>
                    <p>Start a new conversation with your digital twin.</p>
                </div>
            `;
        }
        
        // Recording
        async function toggleRecording() {
            const btn = document.getElementById('recordBtn');
            
            if (isRecording) {
                try {
                    await fetch('/api/recording/stop', { method: 'POST' });
                    btn.textContent = '🔴 Record';
                    btn.classList.remove('active');
                    isRecording = false;
                    showToast('Recording stopped', 'success');
                } catch (e) {
                    showToast('Failed to stop recording', 'error');
                }
            } else {
                try {
                    await fetch('/api/recording/start', { method: 'POST' });
                    btn.textContent = '⏹️ Stop';
                    btn.classList.add('active');
                    isRecording = true;
                    showToast('Recording started', 'success');
                } catch (e) {
                    showToast('Failed to start recording', 'error');
                }
            }
        }
        
        // Toast notifications
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
                <span>${message}</span>
            `;
            
            container.appendChild(toast);
            
            setTimeout(() => toast.remove(), 3000);
        }
        
        // Close modal on outside click
        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                hideSettings();
            }
        });
    </script>
</body>
</html>'''


# ============================================================================
# Server Runner
# ============================================================================

def create_app() -> FastAPI:
    """Create and return the FastAPI application."""
    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the web server."""
    import uvicorn
    uvicorn.run(
        "mnemosyne.web.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server(port=8000, reload=True)
