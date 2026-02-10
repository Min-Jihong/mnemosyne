"""Ollama provider implementation for local models."""

from typing import AsyncIterator

import httpx

from mnemosyne.llm.base import LLMProvider, EmbeddingProvider, Message, Response


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.2",
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    @property
    def name(self) -> str:
        return "ollama"
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert messages to Ollama format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate a completion."""
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model or self.default_model,
                "messages": self._convert_messages(messages),
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return Response(
            content=data["message"]["content"],
            model=data["model"],
            usage={
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
            },
            finish_reason="stop",
        )
    
    async def complete_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate completion with image understanding (requires llava or similar)."""
        import base64
        
        msgs = self._convert_messages(messages)
        
        # Add images to the last user message
        if msgs and images:
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i]["role"] == "user":
                    msgs[i]["images"] = [
                        base64.b64encode(img).decode("utf-8")
                        for img in images
                    ]
                    break
        
        # Use llava model for vision by default
        vision_model = model or "llava"
        
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": vision_model,
                "messages": msgs,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return Response(
            content=data["message"]["content"],
            model=data["model"],
            usage={
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
            },
            finish_reason="stop",
        )
    
    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model or self.default_model,
                "messages": self._convert_messages(messages),
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            import json
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
    
    async def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama local embedding provider."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
        self._dimension = 768  # nomic-embed-text default
    
    @property
    def name(self) -> str:
        return "ollama"
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        embeddings = []
        
        for text in texts:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
        
        return embeddings
    
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
    
    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            
            data = response.json()
            models = [m["name"].split(":")[0] for m in data.get("models", [])]
            return self.model.split(":")[0] in models
        except Exception:
            return False
