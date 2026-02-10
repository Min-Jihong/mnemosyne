import json
from typing import Any

from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.store.models import StoredEvent, Screenshot
from mnemosyne.store.database import Database
from mnemosyne.reason.context import ContextBuilder


class IntentInferrer:
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        database: Database,
        context_builder: ContextBuilder | None = None,
    ):
        self.llm = llm
        self.database = database
        self.context_builder = context_builder or ContextBuilder()
    
    async def infer_intent(
        self,
        event: StoredEvent,
        surrounding_events: list[StoredEvent] | None = None,
        screenshot: Screenshot | None = None,
    ) -> dict[str, Any]:
        if surrounding_events is None:
            surrounding_events = self.database.get_events(
                session_id=event.session_id,
                limit=10,
            )
        
        prompt = self.context_builder.build_prompt(
            event=event,
            surrounding_events=surrounding_events,
            screenshot_path=screenshot.filepath if screenshot else None,
        )
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI that analyzes user behavior on computers. "
                    "Your goal is to understand WHY the user performed each action, "
                    "not just WHAT they did. Think deeply about intent and context."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        
        if screenshot:
            image_data = self.context_builder.encode_screenshot(screenshot.filepath)
            if image_data:
                messages[1]["images"] = [image_data]
        
        response = await self.llm.generate(messages)
        
        try:
            result = self._parse_response(response)
        except Exception:
            result = {
                "intent": response[:200],
                "reasoning": "Failed to parse structured response",
                "confidence": "low",
                "predicted_next": None,
            }
        
        self.database.update_event_intent(
            event_id=event.id,
            inferred_intent=result.get("intent", ""),
            reasoning=result.get("reasoning"),
        )
        
        return result
    
    def _parse_response(self, response: str) -> dict[str, Any]:
        response = response.strip()
        
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])
        
        return json.loads(response)
    
    async def batch_infer(
        self,
        session_id: str,
        batch_size: int = 10,
    ) -> int:
        events = self.database.get_events_without_intent(
            session_id=session_id,
            limit=batch_size,
        )
        
        all_events = self.database.get_events(session_id=session_id, limit=1000)
        
        count = 0
        for event in events:
            idx = next(
                (i for i, e in enumerate(all_events) if e.id == event.id),
                0,
            )
            surrounding = all_events[max(0, idx - 5):idx]
            
            screenshot = None
            if event.screenshot_id:
                screenshot = self.database.get_screenshot(event.screenshot_id)
            
            await self.infer_intent(
                event=event,
                surrounding_events=surrounding,
                screenshot=screenshot,
            )
            count += 1
        
        return count
