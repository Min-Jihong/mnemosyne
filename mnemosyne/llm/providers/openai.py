"""OpenAI provider implementation."""

import base64
from typing import AsyncIterator

import openai

from mnemosyne.llm.base import LLMProvider, EmbeddingProvider, Message, Response


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_model: str = "gpt-4o",
    ):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.default_model = default_model
    
    @property
    def name(self) -> str:
        return "openai"
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert messages to OpenAI format."""
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
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=self._convert_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        choice = response.choices[0]
        return Response(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
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
        """Generate completion with image understanding."""
        msgs = self._convert_messages(messages)
        
        # Add images to the last user message
        if msgs and images:
            image_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(img).decode('utf-8')}",
                    },
                }
                for img in images
            ]
            
            # Find the last user message and add images
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i]["role"] == "user":
                    text_content = msgs[i]["content"]
                    msgs[i]["content"] = image_content + [
                        {"type": "text", "text": text_content}
                    ]
                    break
        
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        choice = response.choices[0]
        return Response(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
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
        stream = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=self._convert_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str | None = None,
    ):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
    
    @property
    def name(self) -> str:
        return "openai"
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimensions.get(self.model, 1536)
