"""Anthropic Claude provider implementation."""

import base64
from typing import AsyncIterator

import anthropic

from mnemosyne.llm.base import LLMProvider, Message, Response


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: str, default_model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = default_model
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert messages to Anthropic format, extracting system message."""
        system_message = None
        converted = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                converted.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        return system_message, converted
    
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate a completion."""
        system, msgs = self._convert_messages(messages)
        
        response = await self.client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or anthropic.NOT_GIVEN,
            messages=msgs,
            **kwargs,
        )
        
        return Response(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
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
        system, msgs = self._convert_messages(messages)
        
        # Add images to the last user message
        if msgs and images:
            image_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(img).decode("utf-8"),
                    },
                }
                for img in images
            ]
            
            # Find the last user message and add images
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i]["role"] == "user":
                    msgs[i]["content"] = image_content + [
                        {"type": "text", "text": msgs[i]["content"]}
                    ]
                    break
        
        response = await self.client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or anthropic.NOT_GIVEN,
            messages=msgs,
            **kwargs,
        )
        
        return Response(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
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
        system, msgs = self._convert_messages(messages)
        
        async with self.client.messages.stream(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or anthropic.NOT_GIVEN,
            messages=msgs,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
