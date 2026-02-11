"""Screen analysis combining capture, OCR, and visual grounding."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from pydantic import BaseModel, Field

from mnemosyne.capture.screen import ScreenCapture
from mnemosyne.grounding import GroundingResult, UIElement, VisualGrounder
from mnemosyne.ocr import OCRExtractor, OCRResult


class ScreenContext(BaseModel):
    """Complete context about the current screen state."""

    screenshot_bytes: bytes = Field(default=b"", description="Raw screenshot bytes")
    screenshot_path: str | None = Field(default=None, description="Path to saved screenshot")
    width: int = Field(default=0, description="Screen width in pixels")
    height: int = Field(default=0, description="Screen height in pixels")

    # OCR results
    text_content: str = Field(default="", description="Extracted text from screen")
    ocr_confidence: float = Field(default=0.0, description="OCR confidence score")

    # Visual grounding results
    elements: list[UIElement] = Field(default_factory=list, description="Detected UI elements")
    annotated_path: str | None = Field(default=None, description="Path to annotated screenshot")

    # Metadata
    timestamp: float = Field(default_factory=time.time, description="Capture timestamp")
    capture_duration_ms: float = Field(default=0.0, description="Time to capture screen")
    analysis_duration_ms: float = Field(default=0.0, description="Time to analyze screen")

    model_config = {"arbitrary_types_allowed": True}

    @property
    def interactive_elements(self) -> list[UIElement]:
        """Get only interactive UI elements."""
        return [e for e in self.elements if e.is_interactive]

    @property
    def element_count(self) -> int:
        """Get total number of detected elements."""
        return len(self.elements)

    def get_element_by_id(self, element_id: int) -> UIElement | None:
        """Get element by its ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None

    def get_element_at_point(self, x: int, y: int) -> UIElement | None:
        """Get the smallest element containing the given point."""
        candidates = [e for e in self.elements if e.contains_point(x, y)]
        if not candidates:
            return None
        return min(candidates, key=lambda e: e.bounds.area)

    def find_elements_by_text(self, text: str, case_sensitive: bool = False) -> list[UIElement]:
        """Find elements whose labels contain the given text."""
        if not case_sensitive:
            text = text.lower()

        results = []
        for element in self.elements:
            label = element.label if case_sensitive else element.label.lower()
            if text in label:
                results.append(element)
        return results


class ScreenAnalyzer:
    """
    Combines screen capture, OCR, and visual grounding for comprehensive screen analysis.

    This class provides a unified interface for:
    - Capturing screenshots
    - Extracting text via OCR
    - Detecting UI elements via visual grounding
    - Finding elements by text or position
    """

    def __init__(
        self,
        output_dir: Path | str | None = None,
        screenshot_quality: int = 80,
        screenshot_format: str = "png",
        ocr_language: str = "eng",
        enable_ocr: bool = True,
        enable_grounding: bool = True,
    ):
        """
        Initialize the screen analyzer.

        Args:
            output_dir: Directory to save screenshots (defaults to ~/.mnemosyne/screenshots)
            screenshot_quality: Image quality (1-100)
            screenshot_format: Image format (png, webp, jpeg)
            ocr_language: Language for OCR (default: eng)
            enable_ocr: Whether to perform OCR on captures
            enable_grounding: Whether to perform visual grounding on captures
        """
        self.output_dir = (
            Path(output_dir) if output_dir else Path.home() / ".mnemosyne" / "screenshots"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._capture = ScreenCapture(
            output_dir=self.output_dir,
            quality=screenshot_quality,
            format=screenshot_format,
        )

        self._ocr = OCRExtractor(language=ocr_language) if enable_ocr else None
        self._grounder = VisualGrounder() if enable_grounding else None

        self._enable_ocr = enable_ocr
        self._enable_grounding = enable_grounding

    async def capture_and_analyze(
        self,
        save_screenshot: bool = True,
        perform_ocr: bool | None = None,
        perform_grounding: bool | None = None,
        annotate: bool = False,
    ) -> ScreenContext:
        """
        Capture the current screen and perform full analysis.

        Args:
            save_screenshot: Whether to save the screenshot to disk
            perform_ocr: Override OCR setting (None uses default)
            perform_grounding: Override grounding setting (None uses default)
            annotate: Whether to create an annotated version of the screenshot

        Returns:
            ScreenContext with all analysis results
        """
        start_time = time.time()

        # Capture screenshot
        capture_start = time.time()
        screenshot_bytes, width, height = await self._capture.capture_async()
        capture_duration = (time.time() - capture_start) * 1000

        # Save screenshot if requested
        screenshot_path: str | None = None
        if save_screenshot:
            timestamp = int(time.time() * 1000)
            filename = f"screen_{timestamp}.{self._capture.format}"
            filepath = self.output_dir / filename
            filepath.write_bytes(screenshot_bytes)
            screenshot_path = str(filepath)

        # Initialize context
        context = ScreenContext(
            screenshot_bytes=screenshot_bytes,
            screenshot_path=screenshot_path,
            width=width,
            height=height,
            capture_duration_ms=capture_duration,
        )

        # Perform OCR if enabled
        do_ocr = perform_ocr if perform_ocr is not None else self._enable_ocr
        if do_ocr and self._ocr and screenshot_path:
            ocr_result = await self._run_ocr(screenshot_path)
            context.text_content = ocr_result.text
            context.ocr_confidence = ocr_result.confidence

        # Perform visual grounding if enabled
        do_grounding = (
            perform_grounding if perform_grounding is not None else self._enable_grounding
        )
        if do_grounding and self._grounder and screenshot_path:
            grounding_result = await self._run_grounding(screenshot_path, annotate)
            context.elements = grounding_result.elements
            context.annotated_path = grounding_result.annotated_path

        context.analysis_duration_ms = (time.time() - start_time) * 1000 - capture_duration
        return context

    async def _run_ocr(self, image_path: str) -> OCRResult:
        """Run OCR on an image asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._ocr.extract_text, image_path)

    async def _run_grounding(self, image_path: str, annotate: bool) -> GroundingResult:
        """Run visual grounding on an image."""
        if annotate:
            return await self._grounder.ground_image(image_path)
        else:
            elements = await self._grounder.detect_elements(image_path)
            return GroundingResult(
                source_path=image_path,
                elements=elements,
            )

    async def find_element_by_text(
        self,
        text: str,
        context: ScreenContext | None = None,
        case_sensitive: bool = False,
    ) -> UIElement | None:
        """
        Find a UI element by its text label.

        Args:
            text: Text to search for in element labels
            context: Existing screen context (captures new if None)
            case_sensitive: Whether to perform case-sensitive matching

        Returns:
            The first matching UIElement, or None if not found
        """
        if context is None:
            context = await self.capture_and_analyze(save_screenshot=False)

        matches = context.find_elements_by_text(text, case_sensitive)
        return matches[0] if matches else None

    async def find_all_elements_by_text(
        self,
        text: str,
        context: ScreenContext | None = None,
        case_sensitive: bool = False,
    ) -> list[UIElement]:
        """
        Find all UI elements matching the given text.

        Args:
            text: Text to search for in element labels
            context: Existing screen context (captures new if None)
            case_sensitive: Whether to perform case-sensitive matching

        Returns:
            List of matching UIElements
        """
        if context is None:
            context = await self.capture_and_analyze(save_screenshot=False)

        return context.find_elements_by_text(text, case_sensitive)

    async def describe_screen(
        self,
        context: ScreenContext | None = None,
        include_text: bool = True,
        include_elements: bool = True,
        max_elements: int = 20,
    ) -> str:
        """
        Generate a text description of the current screen for LLM consumption.

        Args:
            context: Existing screen context (captures new if None)
            include_text: Whether to include OCR text
            include_elements: Whether to include UI element descriptions
            max_elements: Maximum number of elements to describe

        Returns:
            Human-readable description of the screen
        """
        if context is None:
            context = await self.capture_and_analyze(save_screenshot=False)

        lines = [
            f"Screen ({context.width}x{context.height} pixels)",
            "",
        ]

        # Add OCR text if available
        if include_text and context.text_content:
            text_preview = context.text_content[:500]
            if len(context.text_content) > 500:
                text_preview += "..."
            lines.extend(
                [
                    "Visible text on screen:",
                    f'"{text_preview}"',
                    "",
                ]
            )

        # Add UI elements
        if include_elements and context.elements:
            interactive = context.interactive_elements[:max_elements]

            if interactive:
                lines.append(f"Interactive UI elements ({len(interactive)} shown):")
                for element in interactive:
                    cx, cy = element.center
                    label_info = f' "{element.label}"' if element.label else ""
                    lines.append(
                        f"  [{element.id}] {element.element_type.value}{label_info} at ({cx}, {cy})"
                    )
                lines.append("")

        lines.extend(
            [
                "To interact with an element, specify its number.",
                "Example: 'Click element 3' or 'Type in element 5'",
            ]
        )

        return "\n".join(lines)

    async def wait_for_element(
        self,
        text: str,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        case_sensitive: bool = False,
    ) -> bool:
        """
        Wait for a UI element with the given text to appear.

        Args:
            text: Text to search for in element labels
            timeout: Maximum time to wait in seconds
            poll_interval: Time between checks in seconds
            case_sensitive: Whether to perform case-sensitive matching

        Returns:
            True if element was found, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            element = await self.find_element_by_text(
                text,
                case_sensitive=case_sensitive,
            )
            if element is not None:
                return True

            await asyncio.sleep(poll_interval)

        return False

    async def wait_for_text(
        self,
        text: str,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        case_sensitive: bool = False,
    ) -> bool:
        """
        Wait for specific text to appear on screen (via OCR).

        Args:
            text: Text to search for on screen
            timeout: Maximum time to wait in seconds
            poll_interval: Time between checks in seconds
            case_sensitive: Whether to perform case-sensitive matching

        Returns:
            True if text was found, False if timeout
        """
        start_time = time.time()
        search_text = text if case_sensitive else text.lower()

        while time.time() - start_time < timeout:
            context = await self.capture_and_analyze(
                save_screenshot=False,
                perform_grounding=False,
            )

            screen_text = context.text_content if case_sensitive else context.text_content.lower()
            if search_text in screen_text:
                return True

            await asyncio.sleep(poll_interval)

        return False

    async def get_element_at_position(
        self,
        x: int,
        y: int,
        context: ScreenContext | None = None,
    ) -> UIElement | None:
        """
        Get the UI element at a specific screen position.

        Args:
            x: X coordinate
            y: Y coordinate
            context: Existing screen context (captures new if None)

        Returns:
            The smallest UIElement containing the point, or None
        """
        if context is None:
            context = await self.capture_and_analyze(save_screenshot=False)

        return context.get_element_at_point(x, y)

    def capture_sync(self) -> tuple[bytes, int, int]:
        """
        Synchronously capture the current screen.

        Returns:
            Tuple of (screenshot_bytes, width, height)
        """
        return self._capture.capture()

    async def capture_to_file(self, filename: str | None = None) -> Path:
        """
        Capture screenshot and save to file.

        Args:
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to the saved screenshot
        """
        filepath, _, _, _ = await self._capture.capture_to_file_async(filename)
        return filepath
