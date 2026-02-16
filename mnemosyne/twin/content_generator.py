"""Content Generation - Generate code, emails, and documents in the user's style."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    CODE = "code"
    EMAIL = "email"
    DOCUMENT = "document"
    MESSAGE = "message"
    COMMENT = "comment"
    COMMIT_MESSAGE = "commit_message"


class CodeLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CPP = "cpp"
    OTHER = "other"


class StyleProfile(BaseModel):
    naming_convention: str = "snake_case"
    indentation: str = "spaces_4"
    line_length_preference: int = 100
    comment_density: str = "minimal"

    function_style: str = "small_focused"
    error_handling_style: str = "explicit"
    type_annotation_preference: str = "always"

    docstring_style: str = "google"

    vocabulary_preferences: list[str] = Field(default_factory=list)
    phrase_patterns: list[str] = Field(default_factory=list)

    formality_level: float = 0.5
    verbosity_level: float = 0.5

    greeting_style: str = "casual"
    closing_style: str = "friendly"


class GeneratedContent(BaseModel):
    content_type: ContentType
    content: str
    confidence: float
    style_match_score: float

    metadata: dict[str, Any] = Field(default_factory=dict)

    alternatives: list[str] = Field(default_factory=list)

    requires_review: bool = True
    suggested_edits: list[str] = Field(default_factory=list)


class ContentGenerator:
    def __init__(
        self,
        llm: Any = None,
        data_dir: Path | None = None,
    ):
        self.llm = llm
        self.data_dir = data_dir or Path.home() / ".mnemosyne" / "content_gen"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.style_profile = self._load_style_profile()
        self._content_examples: dict[ContentType, list[str]] = {ct: [] for ct in ContentType}
        self._generation_history: list[GeneratedContent] = []

        self._load_examples()

    def _load_style_profile(self) -> StyleProfile:
        profile_path = self.data_dir / "style_profile.json"
        if profile_path.exists():
            try:
                return StyleProfile(**json.loads(profile_path.read_text()))
            except Exception:
                pass
        return StyleProfile()

    def _save_style_profile(self) -> None:
        profile_path = self.data_dir / "style_profile.json"
        profile_path.write_text(self.style_profile.model_dump_json(indent=2))

    def _load_examples(self) -> None:
        examples_path = self.data_dir / "content_examples.json"
        if examples_path.exists():
            try:
                data = json.loads(examples_path.read_text())
                for content_type in ContentType:
                    key = content_type.value
                    if key in data:
                        self._content_examples[content_type] = data[key][:50]
            except Exception:
                pass

    def _save_examples(self) -> None:
        examples_path = self.data_dir / "content_examples.json"
        data = {ct.value: examples[:50] for ct, examples in self._content_examples.items()}
        examples_path.write_text(json.dumps(data, indent=2))

    def learn_from_content(
        self,
        content: str,
        content_type: ContentType,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._content_examples[content_type].append(content)

        if len(self._content_examples[content_type]) > 100:
            self._content_examples[content_type] = self._content_examples[content_type][-100:]

        style_updates = self._analyze_style(content, content_type)
        self._update_style_profile(style_updates)

        self._save_examples()
        self._save_style_profile()

        return {
            "learned": True,
            "content_type": content_type.value,
            "style_updates": style_updates,
            "examples_count": len(self._content_examples[content_type]),
        }

    def _analyze_style(self, content: str, content_type: ContentType) -> dict[str, Any]:
        updates = {}

        if content_type == ContentType.CODE:
            if "    " in content:
                updates["indentation"] = "spaces_4"
            elif "\t" in content:
                updates["indentation"] = "tabs"
            elif "  " in content:
                updates["indentation"] = "spaces_2"

            lines = content.split("\n")
            if lines:
                avg_line_length = sum(len(line) for line in lines) / len(lines)
                max_line_length = max(len(line) for line in lines)
                if max_line_length > 120:
                    updates["line_length_preference"] = 120
                elif max_line_length > 80:
                    updates["line_length_preference"] = 100
                else:
                    updates["line_length_preference"] = 80

            if "def " in content or "class " in content:
                if "_" in content:
                    updates["naming_convention"] = "snake_case"
                elif any(c.isupper() for c in content if c.isalpha()):
                    camel_count = len(
                        [
                            w
                            for w in content.split()
                            if w and w[0].islower() and any(c.isupper() for c in w)
                        ]
                    )
                    if camel_count > 0:
                        updates["naming_convention"] = "camelCase"

        elif content_type == ContentType.EMAIL:
            content_lower = content.lower()

            casual_greetings = ["hi ", "hey ", "hello "]
            formal_greetings = ["dear ", "good morning", "good afternoon"]

            if any(g in content_lower for g in casual_greetings):
                updates["greeting_style"] = "casual"
            elif any(g in content_lower for g in formal_greetings):
                updates["greeting_style"] = "formal"

            casual_closings = ["thanks", "cheers", "best"]
            formal_closings = ["sincerely", "regards", "respectfully"]

            if any(c in content_lower for c in formal_closings):
                updates["closing_style"] = "formal"
            elif any(c in content_lower for c in casual_closings):
                updates["closing_style"] = "casual"

            words = content.split()
            if words:
                avg_word_length = sum(len(w) for w in words) / len(words)
                updates["verbosity_level"] = min(avg_word_length / 10, 1.0)

        return updates

    def _update_style_profile(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if hasattr(self.style_profile, key):
                setattr(self.style_profile, key, value)

    async def generate_code(
        self,
        task_description: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        context: dict[str, Any] | None = None,
        existing_code: str = "",
    ) -> GeneratedContent:
        if not self.llm:
            return GeneratedContent(
                content_type=ContentType.CODE,
                content="# LLM not available",
                confidence=0.0,
                style_match_score=0.0,
            )

        style_instructions = self._build_code_style_instructions(language)
        examples = self._get_relevant_examples(ContentType.CODE, 3)

        system_prompt = f"""You are writing code in the user's personal style.

Style Guidelines:
{style_instructions}

User's code examples for reference:
{chr(10).join(examples[:2]) if examples else "No examples available yet."}

Generate code that:
1. Accomplishes the task correctly
2. Matches the user's coding style exactly
3. Follows their naming conventions and formatting preferences"""

        user_prompt = f"""Task: {task_description}
Language: {language.value}
"""
        if existing_code:
            user_prompt += f"\nExisting code context:\n```\n{existing_code[:1000]}\n```"
        if context:
            user_prompt += f"\nAdditional context: {json.dumps(context)}"

        user_prompt += "\n\nGenerate the code:"

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await self.llm.generate(messages)

            code = self._extract_code_from_response(response)
            style_score = self._calculate_style_match(code, ContentType.CODE)

            result = GeneratedContent(
                content_type=ContentType.CODE,
                content=code,
                confidence=0.8,
                style_match_score=style_score,
                metadata={"language": language.value, "task": task_description},
                requires_review=style_score < 0.7,
            )

            self._generation_history.append(result)
            return result

        except Exception as e:
            return GeneratedContent(
                content_type=ContentType.CODE,
                content=f"# Error generating code: {e}",
                confidence=0.0,
                style_match_score=0.0,
            )

    def _build_code_style_instructions(self, language: CodeLanguage) -> str:
        profile = self.style_profile

        instructions = [
            f"- Naming: {profile.naming_convention}",
            f"- Indentation: {profile.indentation}",
            f"- Line length: ~{profile.line_length_preference} chars",
            f"- Comments: {profile.comment_density}",
            f"- Functions: {profile.function_style}",
            f"- Error handling: {profile.error_handling_style}",
        ]

        if language in (CodeLanguage.PYTHON, CodeLanguage.TYPESCRIPT):
            instructions.append(f"- Type hints: {profile.type_annotation_preference}")

        return "\n".join(instructions)

    def _extract_code_from_response(self, response: str) -> str:
        response = response.strip()

        if "```" in response:
            lines = response.split("\n")
            code_lines = []
            in_code_block = False

            for line in lines:
                if line.startswith("```"):
                    if in_code_block:
                        break
                    in_code_block = True
                    continue
                if in_code_block:
                    code_lines.append(line)

            if code_lines:
                return "\n".join(code_lines)

        return response

    async def generate_email(
        self,
        purpose: str,
        recipient: str = "",
        context: dict[str, Any] | None = None,
        reply_to: str = "",
    ) -> GeneratedContent:
        if not self.llm:
            return GeneratedContent(
                content_type=ContentType.EMAIL,
                content="# LLM not available",
                confidence=0.0,
                style_match_score=0.0,
            )

        style_instructions = self._build_email_style_instructions()
        examples = self._get_relevant_examples(ContentType.EMAIL, 2)

        system_prompt = f"""You are writing an email in the user's personal style.

Style Guidelines:
{style_instructions}

User's email examples for reference:
{chr(10).join(examples) if examples else "No examples available yet."}

Write an email that:
1. Accomplishes the purpose effectively
2. Matches the user's writing style exactly
3. Uses appropriate tone and formality"""

        user_prompt = f"Purpose: {purpose}"
        if recipient:
            user_prompt += f"\nRecipient: {recipient}"
        if reply_to:
            user_prompt += f"\nReplying to:\n{reply_to[:500]}"
        if context:
            user_prompt += f"\nContext: {json.dumps(context)}"

        user_prompt += "\n\nWrite the email:"

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await self.llm.generate(messages)

            style_score = self._calculate_style_match(response, ContentType.EMAIL)

            result = GeneratedContent(
                content_type=ContentType.EMAIL,
                content=response.strip(),
                confidence=0.8,
                style_match_score=style_score,
                metadata={"purpose": purpose, "recipient": recipient},
                requires_review=True,
            )

            self._generation_history.append(result)
            return result

        except Exception as e:
            return GeneratedContent(
                content_type=ContentType.EMAIL,
                content=f"Error generating email: {e}",
                confidence=0.0,
                style_match_score=0.0,
            )

    def _build_email_style_instructions(self) -> str:
        profile = self.style_profile

        return f"""- Greeting style: {profile.greeting_style}
- Closing style: {profile.closing_style}
- Formality level: {"formal" if profile.formality_level > 0.6 else "casual" if profile.formality_level < 0.4 else "balanced"}
- Verbosity: {"concise" if profile.verbosity_level < 0.4 else "detailed" if profile.verbosity_level > 0.6 else "moderate"}"""

    async def generate_document(
        self,
        topic: str,
        document_type: str = "general",
        context: dict[str, Any] | None = None,
        outline: list[str] | None = None,
    ) -> GeneratedContent:
        if not self.llm:
            return GeneratedContent(
                content_type=ContentType.DOCUMENT,
                content="# LLM not available",
                confidence=0.0,
                style_match_score=0.0,
            )

        examples = self._get_relevant_examples(ContentType.DOCUMENT, 2)

        system_prompt = f"""You are writing a document in the user's personal style.

User's document examples for reference:
{chr(10).join(examples) if examples else "No examples available yet."}

Write a document that:
1. Covers the topic thoroughly
2. Matches the user's writing style
3. Is well-organized and clear"""

        user_prompt = f"Topic: {topic}\nType: {document_type}"
        if outline:
            user_prompt += f"\nOutline:\n" + "\n".join(f"- {item}" for item in outline)
        if context:
            user_prompt += f"\nContext: {json.dumps(context)}"

        user_prompt += "\n\nWrite the document:"

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await self.llm.generate(messages)

            style_score = self._calculate_style_match(response, ContentType.DOCUMENT)

            result = GeneratedContent(
                content_type=ContentType.DOCUMENT,
                content=response.strip(),
                confidence=0.8,
                style_match_score=style_score,
                metadata={"topic": topic, "type": document_type},
                requires_review=True,
            )

            self._generation_history.append(result)
            return result

        except Exception as e:
            return GeneratedContent(
                content_type=ContentType.DOCUMENT,
                content=f"Error generating document: {e}",
                confidence=0.0,
                style_match_score=0.0,
            )

    def _get_relevant_examples(self, content_type: ContentType, count: int) -> list[str]:
        examples = self._content_examples.get(content_type, [])
        return examples[-count:] if examples else []

    def _calculate_style_match(self, content: str, content_type: ContentType) -> float:
        if not content:
            return 0.0

        score = 0.5
        profile = self.style_profile

        if content_type == ContentType.CODE:
            if profile.indentation == "spaces_4" and "    " in content:
                score += 0.1
            elif profile.indentation == "tabs" and "\t" in content:
                score += 0.1

            lines = content.split("\n")
            if lines:
                max_len = max(len(line) for line in lines)
                if max_len <= profile.line_length_preference + 20:
                    score += 0.1

            if profile.naming_convention == "snake_case":
                if "_" in content:
                    score += 0.1

        elif content_type == ContentType.EMAIL:
            content_lower = content.lower()

            if profile.greeting_style == "casual":
                if any(g in content_lower for g in ["hi ", "hey ", "hello "]):
                    score += 0.15
            elif profile.greeting_style == "formal":
                if any(g in content_lower for g in ["dear ", "good morning"]):
                    score += 0.15

        return min(score, 1.0)

    def provide_feedback(
        self,
        generation_id: str | None,
        feedback_type: str,
        details: str = "",
    ) -> dict[str, Any]:
        if feedback_type == "style_correction":
            style_updates = self._analyze_style(details, ContentType.CODE)
            self._update_style_profile(style_updates)
            self._save_style_profile()
            return {"updated": True, "changes": style_updates}

        if feedback_type == "example_added":
            content_type = ContentType.CODE
            self._content_examples[content_type].append(details)
            self._save_examples()
            return {"added": True}

        return {"feedback_received": True}

    def get_style_profile(self) -> StyleProfile:
        return self.style_profile

    def get_generation_stats(self) -> dict[str, Any]:
        total = len(self._generation_history)
        by_type = {}
        avg_style_score = 0.0

        for gen in self._generation_history:
            ct = gen.content_type.value
            by_type[ct] = by_type.get(ct, 0) + 1
            avg_style_score += gen.style_match_score

        return {
            "total_generations": total,
            "by_type": by_type,
            "avg_style_match": avg_style_score / total if total > 0 else 0,
            "examples_count": {ct.value: len(ex) for ct, ex in self._content_examples.items()},
        }
