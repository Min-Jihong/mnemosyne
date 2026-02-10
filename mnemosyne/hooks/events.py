"""Hook event types and priorities."""

from enum import Enum, auto


class HookEvent(str, Enum):
    """
    All available hook events in the Mnemosyne lifecycle.

    Events are organized by the subsystem they belong to:
    - CAPTURE_*: Input capture events
    - INFERENCE_*: LLM inference events
    - EXECUTE_*: Action execution events
    - MEMORY_*: Memory operations
    - SESSION_*: Session lifecycle
    - SYSTEM_*: System-level events
    """

    # Capture Events
    PRE_CAPTURE = "pre_capture"
    POST_CAPTURE = "post_capture"
    CAPTURE_ERROR = "capture_error"

    # Inference Events
    PRE_INFERENCE = "pre_inference"
    POST_INFERENCE = "post_inference"
    INFERENCE_ERROR = "inference_error"

    # Execution Events
    PRE_EXECUTE = "pre_execute"
    POST_EXECUTE = "post_execute"
    EXECUTE_ERROR = "execute_error"
    EXECUTE_BLOCKED = "execute_blocked"  # Safety guard triggered

    # Memory Events
    PRE_MEMORY_STORE = "pre_memory_store"
    POST_MEMORY_STORE = "post_memory_store"
    PRE_MEMORY_RETRIEVE = "pre_memory_retrieve"
    POST_MEMORY_RETRIEVE = "post_memory_retrieve"

    # Session Events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_PAUSE = "session_pause"
    SESSION_RESUME = "session_resume"

    # Curiosity Events
    PRE_CURIOSITY = "pre_curiosity"
    POST_CURIOSITY = "post_curiosity"
    QUESTION_GENERATED = "question_generated"

    # Learning Events
    PRE_LEARN = "pre_learn"
    POST_LEARN = "post_learn"
    MODEL_UPDATE = "model_update"

    # System Events
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    CONFIG_CHANGE = "config_change"
    ERROR = "error"

    # Plugin Events
    PLUGIN_LOAD = "plugin_load"
    PLUGIN_UNLOAD = "plugin_unload"
    PLUGIN_ERROR = "plugin_error"


class HookPriority(int, Enum):
    """
    Priority levels for hook handlers.

    Higher priority handlers run first.
    Use sparingly - most hooks should use NORMAL.
    """

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    SYSTEM = 200  # Reserved for internal use


# Event metadata for documentation and validation
HOOK_EVENT_METADATA: dict[HookEvent, dict] = {
    HookEvent.PRE_CAPTURE: {
        "description": "Before capturing input events",
        "payload": {"capture_type": "str", "config": "dict"},
        "can_modify": True,
        "can_cancel": True,
    },
    HookEvent.POST_CAPTURE: {
        "description": "After capturing input events",
        "payload": {"events": "list[Event]", "session_id": "str"},
        "can_modify": True,
        "can_cancel": False,
    },
    HookEvent.PRE_INFERENCE: {
        "description": "Before sending to LLM for inference",
        "payload": {"prompt": "str", "context": "dict", "model": "str"},
        "can_modify": True,
        "can_cancel": True,
    },
    HookEvent.POST_INFERENCE: {
        "description": "After receiving LLM response",
        "payload": {"response": "str", "tokens_used": "int", "latency_ms": "float"},
        "can_modify": True,
        "can_cancel": False,
    },
    HookEvent.PRE_EXECUTE: {
        "description": "Before executing an action",
        "payload": {"action": "Action", "safety_check": "bool"},
        "can_modify": True,
        "can_cancel": True,
    },
    HookEvent.POST_EXECUTE: {
        "description": "After executing an action",
        "payload": {"action": "Action", "result": "ActionResult"},
        "can_modify": False,
        "can_cancel": False,
    },
    HookEvent.SESSION_START: {
        "description": "When a recording session starts",
        "payload": {"session_id": "str", "name": "str", "config": "dict"},
        "can_modify": True,
        "can_cancel": True,
    },
    HookEvent.SESSION_END: {
        "description": "When a recording session ends",
        "payload": {"session_id": "str", "event_count": "int", "duration_seconds": "float"},
        "can_modify": False,
        "can_cancel": False,
    },
    HookEvent.ERROR: {
        "description": "When an error occurs anywhere in the system",
        "payload": {"error": "Exception", "context": "str", "recoverable": "bool"},
        "can_modify": False,
        "can_cancel": False,
    },
}
