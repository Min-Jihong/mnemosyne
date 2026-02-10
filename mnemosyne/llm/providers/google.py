"""Google Gemini provider implementation."""

import base64
from typing import AsyncIterator

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from mnemosyne.llm.base import LLMProvider, EmbeddingProvider, Message, Response


class GoogleProvider(LLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: str, default_model: str = "gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.default_model = default_model
        self._safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    
    @property
    def name(self) -> str:
        return "google"
    
    def _get_model(self, model: str | None = None) -> genai.GenerativeModel:
        """Get a GenerativeModel instance."""
        return genai.GenerativeModel(model or self.default_model)
    
    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert messages to Gemini format."""
        system_instruction = None
        history = []
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                role = "user" if msg.role == "user" else "model"
                history.append({"role": role, "parts": [msg.content]})
        
        return system_instruction, history
    
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Response:
        """Generate a completion."""
        system_instruction, history = self._convert_messages(messages)
        
        gen_model = genai.GenerativeModel(
            model_name=model or self.default_model,
            system_instruction=system_instruction,
            safety_settings=self._safety_settings,
        )
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Start chat with history (except last message)
        chat = gen_model.start_chat(history=history[:-1] if len(history) > 1 else [])
        
        # Send the last message
        last_message = history[-1]["parts"][0] if history else ""
        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
        )
        
        return Response(
            content=response.text,
            model=model or self.default_model,
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
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
        """Generate completion with image understanding."""
        system_instruction, history = self._convert_messages(messages)
        
        gen_model = genai.GenerativeModel(
            model_name=model or self.default_model,
            system_instruction=system_instruction,
            safety_settings=self._safety_settings,
        )
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Create content with images
        parts = []
        for img in images:
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": base64.b64encode(img).decode("utf-8"),
                }
            })
        
        # Add the last text message
        if history:
            parts.append(history[-1]["parts"][0])
        
        response = await gen_model.generate_content_async(
            parts,
            generation_config=generation_config,
        )
        
        return Response(
            content=response.text,
            model=model or self.default_model,
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
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
        system_instruction, history = self._convert_messages(messages)
        
        gen_model = genai.GenerativeModel(
            model_name=model or self.default_model,
            system_instruction=system_instruction,
            safety_settings=self._safety_settings,
        )
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        chat = gen_model.start_chat(history=history[:-1] if len(history) > 1 else [])
        last_message = history[-1]["parts"][0] if history else ""
        
        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
            stream=True,
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text


class GoogleEmbeddingProvider(EmbeddingProvider):
    """Google embedding provider."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        genai.configure(api_key=api_key)
        self.model = model
    
    @property
    def name(self) -> str:
        return "google"
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        # Google's embedding API is synchronous, so we run it directly
        result = genai.embed_content(
            model=f"models/{self.model}",
            content=texts,
            task_type="retrieval_document",
        )
        return result["embedding"] if isinstance(result["embedding"][0], list) else [result["embedding"]]
    
    def dimension(self) -> int:
        """Return embedding dimension."""
        return 768  # text-embedding-004 dimension
