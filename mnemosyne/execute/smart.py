"""Smart executor that orchestrates pattern matching, planning, and execution."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mnemosyne.execute.controller import Controller
from mnemosyne.execute.patterns import ActionPattern, PatternMatcher
from mnemosyne.execute.planner import Action, ActionPlan, ActionPlanner, ActionType
from mnemosyne.execute.safety import SafetyConfig, SafetyGuard
from mnemosyne.execute.screen import ScreenAnalyzer, ScreenContext
from mnemosyne.llm.base import BaseLLMProvider
from mnemosyne.memory.persistent import PersistentMemory


class ExecutionStatus(str, Enum):
    """Status of an execution attempt."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepResult(BaseModel):
    """Result of executing a single action step."""

    action: Action
    success: bool
    error: str | None = None
    duration_ms: float = 0.0
    screenshot_path: str | None = None
    screen_changed: bool = False


class ExecutionResult(BaseModel):
    """Complete result of a goal execution."""

    goal: str
    status: ExecutionStatus
    steps: list[StepResult] = Field(default_factory=list)

    pattern_used: str | None = Field(default=None, description="ID of pattern used, if any")
    plan_generated: bool = Field(default=False, description="Whether a new plan was generated")

    total_duration_ms: float = 0.0
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None

    error: str | None = None
    final_screenshot_path: str | None = None

    @property
    def success(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def successful_steps(self) -> int:
        return sum(1 for s in self.steps if s.success)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if not s.success)


@dataclass
class SmartExecutorConfig:
    """Configuration for SmartExecutor."""

    max_steps: int = 50
    max_retries_per_action: int = 3
    max_plan_adaptations: int = 3

    verify_after_action: bool = True
    collect_evidence: bool = True

    action_delay_ms: int = 100
    verification_delay_ms: int = 500

    require_confirmation: bool = False

    use_patterns: bool = True
    learn_patterns: bool = True
    min_pattern_confidence: float = 0.7


class SmartExecutor:
    """
    Intelligent executor that orchestrates pattern matching, planning, and execution.

    Workflow:
    1. Check for matching patterns
    2. If no pattern, generate plan with LLM
    3. Execute actions with screen verification
    4. Adapt plan on failures
    5. Learn successful patterns
    """

    def __init__(
        self,
        llm: BaseLLMProvider,
        memory: PersistentMemory | None = None,
        data_dir: Path | str | None = None,
        config: SmartExecutorConfig | None = None,
        safety_config: SafetyConfig | None = None,
        on_action: Callable[[Action, StepResult], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ):
        self._llm = llm
        self._memory = memory
        self._config = config or SmartExecutorConfig()

        data_dir = Path(data_dir) if data_dir else Path.home() / ".mnemosyne"

        self._screen = ScreenAnalyzer(output_dir=data_dir / "screenshots")
        self._planner = ActionPlanner(llm=llm)
        self._patterns = PatternMatcher(data_dir=data_dir, memory=memory)
        self._controller = Controller(
            safety_guard=SafetyGuard(config=safety_config),
            action_delay_ms=self._config.action_delay_ms,
        )

        self._on_action = on_action
        self._on_status = on_status

        self._running = False
        self._cancelled = False

    async def execute(
        self,
        goal: str,
        max_steps: int | None = None,
        require_confirmation: bool | None = None,
    ) -> ExecutionResult:
        """
        Execute a goal using pattern matching and LLM planning.

        Args:
            goal: The goal to achieve
            max_steps: Override max steps (uses config default if None)
            require_confirmation: Override confirmation requirement

        Returns:
            ExecutionResult with complete execution details
        """
        max_steps = max_steps or self._config.max_steps
        require_confirmation = (
            require_confirmation
            if require_confirmation is not None
            else self._config.require_confirmation
        )

        self._running = True
        self._cancelled = False

        result = ExecutionResult(
            goal=goal,
            status=ExecutionStatus.RUNNING,
        )

        start_time = time.time()

        try:
            self._emit_status(f"Starting execution: {goal}")

            initial_context = await self._screen.capture_and_analyze(
                save_screenshot=self._config.collect_evidence
            )

            pattern: ActionPattern | None = None
            plan: ActionPlan | None = None
            actions: list[Action] = []

            if self._config.use_patterns:
                self._emit_status("Checking for matching patterns...")
                pattern = await self._patterns.find_matching_pattern(goal, initial_context)

                if pattern and pattern.success_rate >= self._config.min_pattern_confidence:
                    self._emit_status(f"Found pattern with {pattern.success_rate:.0%} success rate")
                    result.pattern_used = pattern.id
                    actions = self._patterns.adapt_pattern(pattern, initial_context)
                else:
                    pattern = None

            if not actions:
                self._emit_status("Generating execution plan...")
                plan = await self._planner.plan_goal(goal, initial_context, max_steps)
                result.plan_generated = True
                actions = plan.actions
                self._emit_status(f"Plan generated with {len(actions)} actions")

            completed_actions: list[Action] = []
            adaptations = 0
            current_context = initial_context

            for step_num, action in enumerate(actions):
                if self._cancelled:
                    result.status = ExecutionStatus.CANCELLED
                    result.error = "Execution cancelled by user"
                    break

                if step_num >= max_steps:
                    result.error = f"Max steps ({max_steps}) reached"
                    break

                if action.type == ActionType.COMPLETE:
                    result.status = ExecutionStatus.COMPLETED
                    break

                if action.type == ActionType.FAIL:
                    result.status = ExecutionStatus.FAILED
                    result.error = action.description or "Plan indicated failure"
                    break

                if require_confirmation:
                    confirmed = await self._confirm_action(action)
                    if not confirmed:
                        continue

                step_result = await self._execute_action(action, current_context)
                result.steps.append(step_result)

                if self._on_action:
                    self._on_action(action, step_result)

                if step_result.success:
                    completed_actions.append(action)

                    if self._config.verify_after_action:
                        await asyncio.sleep(self._config.verification_delay_ms / 1000)
                        current_context = await self._screen.capture_and_analyze(
                            save_screenshot=self._config.collect_evidence
                        )
                        step_result.screenshot_path = current_context.screenshot_path
                else:
                    if adaptations < self._config.max_plan_adaptations and plan:
                        self._emit_status(
                            f"Action failed, adapting plan (attempt {adaptations + 1})"
                        )

                        current_context = await self._screen.capture_and_analyze()
                        plan = await self._planner.adapt_plan(
                            plan, action, step_result.error or "Unknown error", current_context
                        )

                        remaining_actions = plan.actions
                        actions = list(actions[: step_num + 1]) + remaining_actions
                        adaptations += 1
                    else:
                        result.status = ExecutionStatus.FAILED
                        result.error = step_result.error
                        break

            if result.status == ExecutionStatus.RUNNING:
                result.status = ExecutionStatus.COMPLETED

            if self._config.collect_evidence:
                final_context = await self._screen.capture_and_analyze()
                result.final_screenshot_path = final_context.screenshot_path

            if self._config.learn_patterns and completed_actions:
                duration_ms = (time.time() - start_time) * 1000
                await self._patterns.learn_pattern(
                    goal=goal,
                    actions=completed_actions,
                    success=result.success,
                    duration_ms=duration_ms,
                    screen_context=initial_context,
                )

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)

        finally:
            self._running = False
            result.end_time = time.time()
            result.total_duration_ms = (result.end_time - start_time) * 1000

        return result

    async def _execute_action(
        self,
        action: Action,
        context: ScreenContext,
    ) -> StepResult:
        """Execute a single action and return the result."""
        start_time = time.time()

        resolved_action = self._resolve_element_coordinates(action, context)

        self._emit_status(
            f"Executing: {resolved_action.type.value} - {resolved_action.description}"
        )

        try:
            success = await self._dispatch_action(resolved_action)

            duration_ms = (time.time() - start_time) * 1000

            return StepResult(
                action=resolved_action,
                success=success,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return StepResult(
                action=resolved_action,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _resolve_element_coordinates(self, action: Action, context: ScreenContext) -> Action:
        """Resolve element_id to actual coordinates."""
        if action.element_id is not None and (action.x is None or action.y is None):
            element = context.get_element_by_id(action.element_id)
            if element:
                cx, cy = element.center
                return action.model_copy(update={"x": cx, "y": cy})
        return action

    async def _dispatch_action(self, action: Action) -> bool:
        """Dispatch action to the appropriate controller method."""
        params = action.to_controller_params()

        if action.type == ActionType.CLICK:
            return self._controller.click(**params)

        elif action.type == ActionType.DOUBLE_CLICK:
            return self._controller.double_click(
                x=params.get("x"),
                y=params.get("y"),
            )

        elif action.type == ActionType.RIGHT_CLICK:
            return self._controller.right_click(
                x=params.get("x"),
                y=params.get("y"),
            )

        elif action.type == ActionType.TYPE_TEXT:
            return self._controller.type_text(text=params.get("text", ""))

        elif action.type == ActionType.PRESS_KEY:
            return self._controller.press_key(key=params.get("key", ""))

        elif action.type == ActionType.HOTKEY:
            keys = params.get("keys", [])
            return self._controller.hotkey(*keys) if keys else False

        elif action.type == ActionType.SCROLL:
            return self._controller.scroll(
                clicks=params.get("clicks", 0),
                x=params.get("x"),
                y=params.get("y"),
            )

        elif action.type == ActionType.MOVE_MOUSE:
            return self._controller.move_mouse(
                x=params.get("x", 0),
                y=params.get("y", 0),
                duration=params.get("duration", 0.25),
            )

        elif action.type == ActionType.DRAG:
            return self._controller.drag(
                start_x=params.get("start_x", 0),
                start_y=params.get("start_y", 0),
                end_x=params.get("end_x", 0),
                end_y=params.get("end_y", 0),
                duration=params.get("duration", 0.5),
            )

        elif action.type == ActionType.WAIT:
            await asyncio.sleep(action.duration)
            return True

        elif action.type == ActionType.WAIT_FOR_ELEMENT:
            if action.wait_text:
                return await self._screen.wait_for_element(
                    text=action.wait_text,
                    timeout=action.timeout,
                )
            return False

        elif action.type == ActionType.WAIT_FOR_TEXT:
            if action.wait_text:
                return await self._screen.wait_for_text(
                    text=action.wait_text,
                    timeout=action.timeout,
                )
            return False

        elif action.type in (ActionType.COMPLETE, ActionType.FAIL):
            return True

        return False

    async def _confirm_action(self, action: Action) -> bool:
        """Request user confirmation for an action. Override for custom UI."""
        return True

    def _emit_status(self, message: str) -> None:
        """Emit status update."""
        if self._on_status:
            self._on_status(message)

    def cancel(self) -> None:
        """Cancel the current execution."""
        self._cancelled = True

    def pause(self) -> None:
        """Pause execution (via safety guard)."""
        self._controller.safety_guard.pause()

    def resume(self) -> None:
        """Resume execution (via safety guard)."""
        self._controller.safety_guard.resume()

    def emergency_stop(self) -> None:
        """Emergency stop all execution."""
        self._cancelled = True
        self._controller.safety_guard.emergency_stop()

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self._running

    async def describe_current_screen(self) -> str:
        """Get a description of the current screen state."""
        return await self._screen.describe_screen()

    async def get_screen_context(self) -> ScreenContext:
        """Capture and analyze the current screen."""
        return await self._screen.capture_and_analyze()

    def get_pattern_stats(self) -> dict[str, Any]:
        """Get statistics about learned patterns."""
        patterns = self._patterns.get_all_patterns()
        reliable = self._patterns.get_reliable_patterns()

        return {
            "total_patterns": len(patterns),
            "reliable_patterns": len(reliable),
            "total_executions": sum(p.success_count + p.failure_count for p in patterns),
            "total_successes": sum(p.success_count for p in patterns),
        }
