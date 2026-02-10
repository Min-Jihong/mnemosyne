import asyncio
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.llm.factory import create_llm_provider
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.memory.types import MemoryType
from mnemosyne.config.schema import LLMConfig, LLMProvider


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = 0.0


@dataclass
class Conversation:
    id: str
    messages: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


class ChatHandler:

    SYSTEM_PROMPT = """You are Mnemosyne, a digital twin AI that learns to think like the user.

You have access to:
1. The user's behavioral patterns and habits
2. Their memories and past interactions
3. Insights about their preferences and decision-making

Your role is to:
- Answer questions about the user's own behavior and patterns
- Help the user understand themselves better
- Execute tasks the way the user would do them
- Be genuinely curious and ask insightful questions

You are not a generic assistant - you are becoming a digital copy of THIS specific user.
Speak naturally and show genuine curiosity about their behavior patterns.

Available commands the user can give you:
- "record" - Start recording their activity
- "analyze [session]" - Analyze a recorded session
- "remember [something]" - Store something in memory
- "recall [query]" - Search memories
- "execute [goal]" - Execute a goal based on learned behavior
- "status" - Show current status
"""

    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        memory: PersistentMemory | None = None,
        data_dir: Path | None = None,
    ):
        self.llm = llm
        self.memory = memory
        self.data_dir = data_dir or Path.home() / ".mnemosyne"
        self._conversations: dict[str, Conversation] = {}
        self._llm_config: LLMConfig | None = None

    def set_llm_config(self, config: LLMConfig) -> None:
        self._llm_config = config
        self.llm = create_llm_provider(config)

    def set_api_key(self, provider: str, api_key: str, model: str | None = None) -> None:
        provider_enum = LLMProvider(provider.lower())

        default_models = {
            LLMProvider.OPENAI: "gpt-4-turbo-preview",
            LLMProvider.ANTHROPIC: "claude-3-opus-20240229",
            LLMProvider.GOOGLE: "gemini-pro",
            LLMProvider.OLLAMA: "llama2",
        }

        config = LLMConfig(
            provider=provider_enum,
            api_key=api_key,
            model=model or default_models.get(provider_enum, "gpt-4"),
        )

        self.set_llm_config(config)
        self._save_config(config)

    def _save_config(self, config: LLMConfig) -> None:
        config_path = self.data_dir / "config.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        existing = {}
        if config_path.exists():
            with open(config_path) as f:
                existing = json.load(f)

        existing["llm"] = {
            "provider": config.provider.value,
            "model": config.model,
            "api_key": config.api_key,
        }

        with open(config_path, "w") as f:
            json.dump(existing, f, indent=2)

    def _load_config(self) -> LLMConfig | None:
        config_path = self.data_dir / "config.json"
        if not config_path.exists():
            return None

        try:
            with open(config_path) as f:
                data = json.load(f)

            if "llm" in data:
                return LLMConfig(
                    provider=LLMProvider(data["llm"]["provider"]),
                    model=data["llm"]["model"],
                    api_key=data["llm"]["api_key"],
                )
        except Exception:
            pass
        return None

    def ensure_llm(self) -> bool:
        if self.llm is not None:
            return True

        config = self._load_config()
        if config:
            self.set_llm_config(config)
            return True

        return False

    async def chat(
        self,
        message: str,
        conversation_id: str = "default",
    ) -> str:
        if not self.ensure_llm():
            return (
                "⚠️ LLM not configured. Please set your API key first.\n\n"
                "You can configure it via:\n"
                "- Web UI: Click 'Settings' and enter your API key\n"
                "- CLI: Run `mnemosyne setup`\n"
                "- API: POST /api/settings with your provider and API key"
            )

        if conversation_id not in self._conversations:
            import uuid
            self._conversations[conversation_id] = Conversation(
                id=conversation_id or str(uuid.uuid4())
            )

        conv = self._conversations[conversation_id]

        import time
        conv.messages.append(Message(
            role="user",
            content=message,
            timestamp=time.time(),
        ))

        command_response = await self._handle_command(message)
        if command_response:
            conv.messages.append(Message(
                role="assistant",
                content=command_response,
                timestamp=time.time(),
            ))
            return command_response

        relevant_memories = []
        if self.memory:
            relevant_memories = self.memory.recall(query=message, n_results=5)

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if relevant_memories:
            memory_context = "\n".join([
                f"- [{m.type.value}] {m.content[:200]}"
                for m in relevant_memories
            ])
            messages.append({
                "role": "system",
                "content": f"Relevant memories about the user:\n{memory_context}",
            })

        for msg in conv.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        try:
            response = await self.llm.generate(messages)
        except Exception as e:
            response = f"Error generating response: {str(e)}"

        conv.messages.append(Message(
            role="assistant",
            content=response,
            timestamp=time.time(),
        ))

        if self.memory:
            self.memory.remember_conversation(
                user_message=message,
                assistant_response=response,
            )

        return response

    async def _handle_command(self, message: str) -> str | None:
        message_lower = message.lower().strip()

        if message_lower == "status":
            return self._get_status()

        if message_lower.startswith("remember "):
            content = message[9:].strip()
            if self.memory:
                self.memory.remember(
                    content=content,
                    memory_type=MemoryType.OBSERVATION,
                    importance=0.7,
                )
                return f"✅ Remembered: \"{content}\""
            return "⚠️ Memory system not initialized."

        if message_lower.startswith("recall "):
            query = message[7:].strip()
            if self.memory:
                memories = self.memory.recall(query=query, n_results=5)
                if memories:
                    result = "🧠 Found memories:\n\n"
                    for i, m in enumerate(memories, 1):
                        result += f"{i}. [{m.type.value}] {m.content[:100]}...\n"
                    return result
                return "No matching memories found."
            return "⚠️ Memory system not initialized."

        return None

    def _get_status(self) -> str:
        status_lines = ["📊 **Mnemosyne Status**\n"]

        if self._llm_config:
            status_lines.append(f"🤖 LLM: {self._llm_config.provider.value} ({self._llm_config.model})")
        else:
            status_lines.append("🤖 LLM: Not configured")

        if self.memory:
            count = self.memory.count()
            status_lines.append(f"🧠 Memories: {count}")
        else:
            status_lines.append("🧠 Memory: Not initialized")

        status_lines.append(f"📁 Data directory: {self.data_dir}")

        return "\n".join(status_lines)

    def get_conversation_history(self, conversation_id: str = "default") -> list[dict]:
        if conversation_id not in self._conversations:
            return []

        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
            for msg in self._conversations[conversation_id].messages
        ]

    def clear_conversation(self, conversation_id: str = "default") -> None:
        if conversation_id in self._conversations:
            self._conversations[conversation_id].messages.clear()
