import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from mnemosyne.execute.controller import Controller
from mnemosyne.execute.safety import SafetyGuard, SafetyConfig
from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.memory.persistent import PersistentMemory
from mnemosyne.memory.types import MemoryType


@dataclass
class AgentState:
    running: bool = False
    current_goal: str = ""
    completed_actions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ExecutionAgent:
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        memory: PersistentMemory,
        controller: Controller | None = None,
        safety_config: SafetyConfig | None = None,
        on_action: Callable[[str, dict], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        self.llm = llm
        self.memory = memory
        self.controller = controller or Controller(
            safety_guard=SafetyGuard(config=safety_config)
        )
        self.on_action = on_action
        self.on_error = on_error
        self.state = AgentState()
    
    async def execute_goal(
        self,
        goal: str,
        max_steps: int = 50,
        require_confirmation: bool = True,
    ) -> dict[str, Any]:
        self.state = AgentState(running=True, current_goal=goal)
        
        self.memory.remember_command(
            command=f"Execute goal: {goal}",
            context={"type": "goal_start"},
        )
        
        relevant_memories = self.memory.recall(
            query=goal,
            n_results=5,
            memory_types=[MemoryType.PATTERN, MemoryType.INSIGHT],
        )
        
        context = self._build_context(goal, relevant_memories)
        
        for step in range(max_steps):
            if not self.state.running:
                break
            
            try:
                action = await self._plan_next_action(context)
                
                if action.get("type") == "complete":
                    break
                
                if require_confirmation:
                    confirmed = await self._confirm_action(action)
                    if not confirmed:
                        continue
                
                success = await self._execute_action(action)
                
                if success:
                    self.state.completed_actions.append(action)
                    context = self._update_context(context, action, success=True)
                else:
                    self.state.errors.append(f"Failed to execute: {action}")
                    context = self._update_context(context, action, success=False)
                    
            except Exception as e:
                error_msg = str(e)
                self.state.errors.append(error_msg)
                if self.on_error:
                    self.on_error(error_msg)
        
        self.state.running = False
        
        result = {
            "goal": goal,
            "completed": len(self.state.errors) == 0,
            "actions_taken": len(self.state.completed_actions),
            "errors": self.state.errors,
        }
        
        self.memory.remember_command(
            command=f"Goal completed: {goal}",
            result=str(result),
            context={"type": "goal_complete"},
        )
        
        return result
    
    def _build_context(
        self,
        goal: str,
        memories: list,
    ) -> dict[str, Any]:
        screen_size = self.controller.get_screen_size()
        mouse_pos = self.controller.get_mouse_position()
        
        return {
            "goal": goal,
            "screen_size": screen_size,
            "mouse_position": mouse_pos,
            "relevant_memories": [m.content for m in memories],
            "actions_taken": [],
            "last_result": None,
        }
    
    def _update_context(
        self,
        context: dict[str, Any],
        action: dict[str, Any],
        success: bool,
    ) -> dict[str, Any]:
        context["actions_taken"].append({
            "action": action,
            "success": success,
        })
        context["last_result"] = "success" if success else "failure"
        context["mouse_position"] = self.controller.get_mouse_position()
        return context
    
    async def _plan_next_action(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        prompt = self._build_planning_prompt(context)
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI agent that controls a computer to achieve goals. "
                    "Plan the next action to take. Return a JSON object with the action. "
                    "Available actions: click, double_click, right_click, type_text, "
                    "press_key, hotkey, scroll, move_mouse, complete. "
                    "Include coordinates (x, y) for mouse actions."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        
        response = await self.llm.generate(messages)
        return self._parse_action(response)
    
    def _build_planning_prompt(self, context: dict[str, Any]) -> str:
        lines = [
            f"Goal: {context['goal']}",
            f"Screen size: {context['screen_size']}",
            f"Current mouse position: {context['mouse_position']}",
            "",
        ]
        
        if context["relevant_memories"]:
            lines.append("Relevant past experiences:")
            for mem in context["relevant_memories"][:3]:
                lines.append(f"  - {mem[:100]}")
            lines.append("")
        
        if context["actions_taken"]:
            lines.append("Actions taken so far:")
            for item in context["actions_taken"][-5:]:
                status = "OK" if item["success"] else "FAILED"
                lines.append(f"  - [{status}] {item['action'].get('type', 'unknown')}")
            lines.append("")
        
        lines.extend([
            "What is the next action to take?",
            "Return JSON: {\"type\": \"action_name\", ...params}",
            "Use {\"type\": \"complete\"} when the goal is achieved.",
        ])
        
        return "\n".join(lines)
    
    def _parse_action(self, response: str) -> dict[str, Any]:
        import json
        
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"type": "unknown", "raw": response}
    
    async def _confirm_action(self, action: dict[str, Any]) -> bool:
        return True
    
    async def _execute_action(self, action: dict[str, Any]) -> bool:
        action_type = action.get("type", "")
        
        if self.on_action:
            self.on_action(action_type, action)
        
        try:
            if action_type == "click":
                return self.controller.click(
                    x=action.get("x"),
                    y=action.get("y"),
                    button=action.get("button", "left"),
                )
            
            elif action_type == "double_click":
                return self.controller.double_click(
                    x=action.get("x"),
                    y=action.get("y"),
                )
            
            elif action_type == "right_click":
                return self.controller.right_click(
                    x=action.get("x"),
                    y=action.get("y"),
                )
            
            elif action_type == "type_text":
                return self.controller.type_text(
                    text=action.get("text", ""),
                    interval=action.get("interval", 0.02),
                )
            
            elif action_type == "press_key":
                return self.controller.press_key(
                    key=action.get("key", ""),
                )
            
            elif action_type == "hotkey":
                keys = action.get("keys", [])
                return self.controller.hotkey(*keys)
            
            elif action_type == "scroll":
                return self.controller.scroll(
                    clicks=action.get("clicks", 0),
                    x=action.get("x"),
                    y=action.get("y"),
                )
            
            elif action_type == "move_mouse":
                return self.controller.move_mouse(
                    x=action.get("x", 0),
                    y=action.get("y", 0),
                    duration=action.get("duration", 0.25),
                )
            
            elif action_type == "complete":
                return True
            
            else:
                return False
                
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
            return False
    
    def stop(self) -> None:
        self.state.running = False
        self.controller.safety_guard.emergency_stop()
    
    def pause(self) -> None:
        self.controller.safety_guard.pause()
    
    def resume(self) -> None:
        self.controller.safety_guard.resume()
