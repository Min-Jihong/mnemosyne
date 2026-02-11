"""LLM-based action planning for goal-oriented execution."""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from mnemosyne.execute.screen import ScreenContext
from mnemosyne.llm.base import BaseLLMProvider, Message


class ActionType(str, Enum):
    """Types of actions the executor can perform."""

    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    MOVE_MOUSE = "move_mouse"
    DRAG = "drag"
    WAIT = "wait"
    WAIT_FOR_ELEMENT = "wait_for_element"
    WAIT_FOR_TEXT = "wait_for_text"
    COMPLETE = "complete"
    FAIL = "fail"


class Action(BaseModel):
    """A single action to be executed."""

    type: ActionType = Field(description="Type of action to perform")

    # Mouse action parameters
    x: int | None = Field(default=None, description="X coordinate for mouse actions")
    y: int | None = Field(default=None, description="Y coordinate for mouse actions")
    element_id: int | None = Field(default=None, description="UI element ID to interact with")
    button: str = Field(default="left", description="Mouse button (left, right, middle)")

    # Keyboard action parameters
    text: str | None = Field(default=None, description="Text to type")
    key: str | None = Field(default=None, description="Key to press")
    keys: list[str] = Field(default_factory=list, description="Keys for hotkey combination")

    # Scroll parameters
    clicks: int = Field(default=0, description="Scroll clicks (positive=up, negative=down)")

    # Drag parameters
    end_x: int | None = Field(default=None, description="End X coordinate for drag")
    end_y: int | None = Field(default=None, description="End Y coordinate for drag")

    # Wait parameters
    duration: float = Field(default=0.5, description="Duration for wait/move actions")
    timeout: float = Field(default=10.0, description="Timeout for wait_for_* actions")
    wait_text: str | None = Field(default=None, description="Text to wait for")

    # Metadata
    description: str = Field(default="", description="Human-readable description of the action")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Planner confidence")
    reasoning: str = Field(default="", description="Why this action was chosen")

    def to_controller_params(self) -> dict[str, Any]:
        """Convert action to parameters for Controller methods."""
        params: dict[str, Any] = {}

        if self.type in (ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK):
            if self.x is not None:
                params["x"] = self.x
            if self.y is not None:
                params["y"] = self.y
            if self.type == ActionType.CLICK:
                params["button"] = self.button

        elif self.type == ActionType.TYPE_TEXT:
            params["text"] = self.text or ""

        elif self.type == ActionType.PRESS_KEY:
            params["key"] = self.key or ""

        elif self.type == ActionType.HOTKEY:
            params["keys"] = self.keys

        elif self.type == ActionType.SCROLL:
            params["clicks"] = self.clicks
            if self.x is not None:
                params["x"] = self.x
            if self.y is not None:
                params["y"] = self.y

        elif self.type == ActionType.MOVE_MOUSE:
            params["x"] = self.x or 0
            params["y"] = self.y or 0
            params["duration"] = self.duration

        elif self.type == ActionType.DRAG:
            params["start_x"] = self.x or 0
            params["start_y"] = self.y or 0
            params["end_x"] = self.end_x or 0
            params["end_y"] = self.end_y or 0
            params["duration"] = self.duration

        return params


class ActionPlan(BaseModel):
    """A sequence of actions to achieve a goal."""

    goal: str = Field(description="The goal this plan aims to achieve")
    actions: list[Action] = Field(default_factory=list, description="Ordered list of actions")
    estimated_duration_seconds: float = Field(default=0.0, description="Estimated execution time")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall plan confidence")
    reasoning: str = Field(default="", description="Explanation of the planning approach")

    @property
    def action_count(self) -> int:
        return len(self.actions)

    @property
    def is_complete(self) -> bool:
        return any(a.type == ActionType.COMPLETE for a in self.actions)

    def get_next_action(self, completed_count: int) -> Action | None:
        """Get the next action to execute."""
        if completed_count >= len(self.actions):
            return None
        return self.actions[completed_count]


PLANNING_SYSTEM_PROMPT = """You are an AI agent that plans computer actions to achieve goals.
You analyze the current screen state and plan the next action(s) to take.

Available action types:
- click: Click at coordinates (x, y) or on element_id
- double_click: Double-click at coordinates
- right_click: Right-click at coordinates
- type_text: Type text string
- press_key: Press a single key (enter, tab, escape, etc.)
- hotkey: Press key combination (e.g., ["cmd", "c"] for copy)
- scroll: Scroll up (positive) or down (negative)
- move_mouse: Move mouse to coordinates
- drag: Drag from (x, y) to (end_x, end_y)
- wait: Wait for duration seconds
- wait_for_element: Wait for UI element with text
- wait_for_text: Wait for text to appear on screen
- complete: Goal has been achieved
- fail: Goal cannot be achieved

When planning:
1. Analyze the screen context carefully
2. Identify the most direct path to the goal
3. Prefer clicking on identified UI elements (use element_id when available)
4. Include wait actions when expecting screen changes
5. Be specific about coordinates or element IDs

Return your response as valid JSON."""


class ActionPlanner:
    """Plans actions to achieve goals using LLM reasoning."""

    def __init__(
        self,
        llm: BaseLLMProvider,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ):
        self._llm = llm
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def plan_goal(
        self,
        goal: str,
        screen_context: ScreenContext,
        max_actions: int = 10,
    ) -> ActionPlan:
        """
        Create a complete action plan to achieve a goal.

        Args:
            goal: The goal to achieve
            screen_context: Current screen state
            max_actions: Maximum number of actions to plan

        Returns:
            ActionPlan with sequence of actions
        """
        screen_description = self._format_screen_context(screen_context)

        prompt = f"""Goal: {goal}

Current screen state:
{screen_description}

Plan a sequence of actions (up to {max_actions}) to achieve this goal.
Return JSON in this format:
{{
    "reasoning": "explanation of your approach",
    "confidence": 0.0-1.0,
    "estimated_duration_seconds": number,
    "actions": [
        {{
            "type": "action_type",
            "description": "what this action does",
            "reasoning": "why this action",
            "confidence": 0.0-1.0,
            ... action-specific parameters ...
        }}
    ]
}}

If the goal appears already achieved, return a single "complete" action.
If the goal cannot be achieved from current state, return a single "fail" action with reasoning."""

        messages = [
            Message(role="system", content=PLANNING_SYSTEM_PROMPT),
            Message(role="user", content=prompt),
        ]

        response = await self._llm.complete(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        return self._parse_plan_response(goal, response.content)

    async def plan_next_action(
        self,
        goal: str,
        screen_context: ScreenContext,
        completed_actions: list[Action],
    ) -> Action:
        """
        Plan the next single action based on current state and progress.

        Args:
            goal: The goal to achieve
            screen_context: Current screen state
            completed_actions: Actions already executed

        Returns:
            The next Action to execute
        """
        screen_description = self._format_screen_context(screen_context)

        history = ""
        if completed_actions:
            history = "\n\nActions completed so far:\n"
            for i, action in enumerate(completed_actions[-5:], 1):
                history += f"{i}. {action.type.value}: {action.description}\n"

        prompt = f"""Goal: {goal}

Current screen state:
{screen_description}
{history}
What is the single next action to take?
Return JSON for ONE action:
{{
    "type": "action_type",
    "description": "what this action does",
    "reasoning": "why this action",
    "confidence": 0.0-1.0,
    ... action-specific parameters ...
}}

Use "complete" if the goal is achieved.
Use "fail" if the goal cannot be achieved."""

        messages = [
            Message(role="system", content=PLANNING_SYSTEM_PROMPT),
            Message(role="user", content=prompt),
        ]

        response = await self._llm.complete(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        return self._parse_action_response(response.content)

    async def adapt_plan(
        self,
        original_plan: ActionPlan,
        failed_action: Action,
        error: str,
        screen_context: ScreenContext,
    ) -> ActionPlan:
        """
        Adapt a plan after an action failure.

        Args:
            original_plan: The plan that was being executed
            failed_action: The action that failed
            error: Error message from the failure
            screen_context: Current screen state after failure

        Returns:
            New ActionPlan adapted to handle the failure
        """
        screen_description = self._format_screen_context(screen_context)

        prompt = f"""Goal: {original_plan.goal}

Original plan reasoning: {original_plan.reasoning}

Failed action:
- Type: {failed_action.type.value}
- Description: {failed_action.description}
- Error: {error}

Current screen state after failure:
{screen_description}

Create a new plan to achieve the goal, adapting to the failure.
Consider:
1. Why the action might have failed
2. Alternative approaches to achieve the same result
3. Whether the goal is still achievable

Return JSON in the same format as before."""

        messages = [
            Message(role="system", content=PLANNING_SYSTEM_PROMPT),
            Message(role="user", content=prompt),
        ]

        response = await self._llm.complete(
            messages=messages,
            model=self._model,
            temperature=self._temperature + 0.1,  # Slightly more creative for adaptation
            max_tokens=self._max_tokens,
        )

        return self._parse_plan_response(original_plan.goal, response.content)

    def _format_screen_context(self, context: ScreenContext) -> str:
        """Format screen context for LLM consumption."""
        lines = [
            f"Screen size: {context.width}x{context.height}",
        ]

        if context.text_content:
            text_preview = context.text_content[:300]
            if len(context.text_content) > 300:
                text_preview += "..."
            lines.append(f"\nVisible text:\n{text_preview}")

        if context.elements:
            lines.append(f"\nUI Elements ({len(context.elements)} detected):")
            for element in context.interactive_elements[:15]:
                cx, cy = element.center
                label = f' "{element.label}"' if element.label else ""
                lines.append(
                    f"  [{element.id}] {element.element_type.value}{label} at ({cx}, {cy})"
                )

        return "\n".join(lines)

    def _parse_plan_response(self, goal: str, response: str) -> ActionPlan:
        """Parse LLM response into ActionPlan."""
        json_data = self._extract_json(response)

        if not json_data:
            return ActionPlan(
                goal=goal,
                actions=[Action(type=ActionType.FAIL, description="Failed to parse plan")],
                confidence=0.0,
                reasoning="Could not parse LLM response",
            )

        actions = []
        for action_data in json_data.get("actions", []):
            action = self._parse_action_data(action_data)
            if action:
                actions.append(action)

        return ActionPlan(
            goal=goal,
            actions=actions,
            estimated_duration_seconds=json_data.get("estimated_duration_seconds", 0.0),
            confidence=json_data.get("confidence", 0.5),
            reasoning=json_data.get("reasoning", ""),
        )

    def _parse_action_response(self, response: str) -> Action:
        """Parse LLM response into single Action."""
        json_data = self._extract_json(response)

        if not json_data:
            return Action(
                type=ActionType.FAIL,
                description="Failed to parse action",
                confidence=0.0,
            )

        action = self._parse_action_data(json_data)
        return action or Action(
            type=ActionType.FAIL,
            description="Invalid action data",
            confidence=0.0,
        )

    def _parse_action_data(self, data: dict[str, Any]) -> Action | None:
        """Parse action data dictionary into Action object."""
        try:
            action_type_str = data.get("type", "").lower()

            try:
                action_type = ActionType(action_type_str)
            except ValueError:
                return None

            return Action(
                type=action_type,
                x=data.get("x"),
                y=data.get("y"),
                element_id=data.get("element_id"),
                button=data.get("button", "left"),
                text=data.get("text"),
                key=data.get("key"),
                keys=data.get("keys", []),
                clicks=data.get("clicks", 0),
                end_x=data.get("end_x"),
                end_y=data.get("end_y"),
                duration=data.get("duration", 0.5),
                timeout=data.get("timeout", 10.0),
                wait_text=data.get("wait_text"),
                description=data.get("description", ""),
                confidence=data.get("confidence", 0.5),
                reasoning=data.get("reasoning", ""),
            )
        except Exception:
            return None

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Extract JSON from LLM response text."""
        text = text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code blocks
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON object
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None
