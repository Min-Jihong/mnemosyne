"""Privacy scrubbing module for PII detection and masking.

This module provides tools for detecting and masking personally identifiable
information (PII) in text, images, and event data.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import asyncio
import re

from pydantic import BaseModel, Field

from mnemosyne.privacy.patterns import (
    PIICategory,
    PIIType,
    PIIPattern,
    PatternConfig,
    PatternMatcher,
    AllowListEntry,
    get_default_patterns,
    get_patterns_by_level,
)


class ScrubLevel(str, Enum):
    """Scrubbing intensity levels."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class PrivacyConfig(BaseModel):
    """Configuration for privacy scrubbing."""
    enabled: bool = True
    level: ScrubLevel = ScrubLevel.STANDARD
    scrub_text: bool = True
    scrub_images: bool = True
    scrub_events: bool = True
    allow_list: list[str] = Field(default_factory=list)
    disabled_types: list[str] = Field(default_factory=list)
    blur_radius: int = Field(default=20, ge=5, le=100)
    ocr_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


@dataclass
class ScrubResult:
    """Result of a scrubbing operation."""
    original_length: int
    scrubbed_length: int
    pii_found: list[tuple[PIIType, str]]
    pii_count: int
    categories_found: set[PIICategory]
    
    @property
    def had_pii(self) -> bool:
        return self.pii_count > 0


@dataclass
class ImageScrubResult:
    """Result of image scrubbing."""
    original_path: Path
    scrubbed_path: Path
    regions_blurred: int
    pii_types_found: list[PIIType]
    ocr_text: str


class PrivacyScrubber:
    """
    Main class for scrubbing PII from various data types.
    
    Supports text, images (via OCR + blur), and event dictionaries.
    """
    
    def __init__(
        self,
        config: PrivacyConfig | None = None,
        output_dir: Path | None = None,
    ):
        self.config = config or PrivacyConfig()
        self.output_dir = output_dir or Path.home() / ".mnemosyne" / "scrubbed"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        pattern_config = PatternConfig(
            allow_list=[
                AllowListEntry(pattern=p) for p in self.config.allow_list
            ],
            disabled_types={
                PIIType(t) for t in self.config.disabled_types
                if t in [e.value for e in PIIType]
            },
        )
        
        patterns = get_patterns_by_level(self.config.level.value)
        self._matcher = PatternMatcher(patterns=patterns, config=pattern_config)
    
    async def scrub_text(self, text: str) -> tuple[str, ScrubResult]:
        """
        Scrub PII from text.
        
        Args:
            text: Text to scrub
            
        Returns:
            Tuple of (scrubbed_text, ScrubResult)
        """
        if not self.config.enabled or not self.config.scrub_text:
            return text, ScrubResult(
                original_length=len(text),
                scrubbed_length=len(text),
                pii_found=[],
                pii_count=0,
                categories_found=set(),
            )
        
        scrubbed, pii_found = self._matcher.scrub(text)
        
        categories = set()
        for pii_type, _ in pii_found:
            for pattern in self._matcher.patterns:
                if pattern.pii_type == pii_type:
                    categories.add(pattern.category)
                    break
        
        return scrubbed, ScrubResult(
            original_length=len(text),
            scrubbed_length=len(scrubbed),
            pii_found=pii_found,
            pii_count=len(pii_found),
            categories_found=categories,
        )
    
    def scrub_text_sync(self, text: str) -> tuple[str, ScrubResult]:
        """Synchronous version of scrub_text."""
        return asyncio.get_event_loop().run_until_complete(self.scrub_text(text))
    
    async def scrub_image(self, image_path: Path) -> ImageScrubResult:
        """
        Scrub PII from an image using OCR detection and blurring.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ImageScrubResult with scrubbed image path
        """
        if not self.config.enabled or not self.config.scrub_images:
            return ImageScrubResult(
                original_path=image_path,
                scrubbed_path=image_path,
                regions_blurred=0,
                pii_types_found=[],
                ocr_text="",
            )
        
        try:
            from PIL import Image, ImageFilter
            HAS_PIL = True
        except ImportError:
            HAS_PIL = False
        
        if not HAS_PIL:
            return ImageScrubResult(
                original_path=image_path,
                scrubbed_path=image_path,
                regions_blurred=0,
                pii_types_found=[],
                ocr_text="",
            )
        
        ocr_data = await self._extract_ocr_with_bounds(image_path)
        
        if not ocr_data:
            return ImageScrubResult(
                original_path=image_path,
                scrubbed_path=image_path,
                regions_blurred=0,
                pii_types_found=[],
                ocr_text="",
            )
        
        full_text = " ".join(item["text"] for item in ocr_data)
        matches = self._matcher.find_matches(full_text)
        
        if not matches:
            return ImageScrubResult(
                original_path=image_path,
                scrubbed_path=image_path,
                regions_blurred=0,
                pii_types_found=[],
                ocr_text=full_text,
            )
        
        matched_texts = {m[1].group(0).lower() for m in matches}
        pii_types = list({m[0].pii_type for m in matches})
        
        regions_to_blur: list[tuple[int, int, int, int]] = []
        for item in ocr_data:
            if item["text"].lower() in matched_texts or any(
                mt in item["text"].lower() for mt in matched_texts
            ):
                regions_to_blur.append(item["bounds"])
        
        if not regions_to_blur:
            for item in ocr_data:
                item_matches = self._matcher.find_matches(item["text"])
                if item_matches:
                    regions_to_blur.append(item["bounds"])
        
        img = Image.open(image_path)
        
        for bounds in regions_to_blur:
            x, y, w, h = bounds
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.width - x, w + 2 * padding)
            h = min(img.height - y, h + 2 * padding)
            
            region = img.crop((x, y, x + w, y + h))
            blurred = region.filter(ImageFilter.GaussianBlur(self.config.blur_radius))
            img.paste(blurred, (x, y))
        
        scrubbed_path = self.output_dir / f"scrubbed_{image_path.name}"
        img.save(scrubbed_path)
        
        return ImageScrubResult(
            original_path=image_path,
            scrubbed_path=scrubbed_path,
            regions_blurred=len(regions_to_blur),
            pii_types_found=pii_types,
            ocr_text=full_text,
        )
    
    async def _extract_ocr_with_bounds(
        self, image_path: Path
    ) -> list[dict[str, Any]]:
        """Extract text with bounding boxes from image."""
        try:
            import pytesseract
            from PIL import Image
            HAS_TESSERACT = True
        except ImportError:
            HAS_TESSERACT = False
        
        if not HAS_TESSERACT:
            return []
        
        try:
            image = Image.open(image_path)
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
            )
            
            results = []
            for i, text in enumerate(data["text"]):
                conf = float(data["conf"][i])
                if conf >= self.config.ocr_confidence_threshold * 100 and text.strip():
                    results.append({
                        "text": text,
                        "bounds": (
                            data["left"][i],
                            data["top"][i],
                            data["width"][i],
                            data["height"][i],
                        ),
                        "confidence": conf / 100.0,
                    })
            
            return results
        except Exception:
            return []
    
    async def scrub_event(self, event: dict[str, Any]) -> tuple[dict[str, Any], ScrubResult]:
        """
        Scrub PII from an event dictionary.
        
        Recursively processes all string values in the event.
        
        Args:
            event: Event dictionary to scrub
            
        Returns:
            Tuple of (scrubbed_event, ScrubResult)
        """
        if not self.config.enabled or not self.config.scrub_events:
            return event, ScrubResult(
                original_length=0,
                scrubbed_length=0,
                pii_found=[],
                pii_count=0,
                categories_found=set(),
            )
        
        all_pii: list[tuple[PIIType, str]] = []
        all_categories: set[PIICategory] = set()
        original_len = 0
        scrubbed_len = 0
        
        async def scrub_value(value: Any) -> Any:
            nonlocal all_pii, all_categories, original_len, scrubbed_len
            
            if isinstance(value, str):
                original_len += len(value)
                scrubbed, result = await self.scrub_text(value)
                scrubbed_len += len(scrubbed)
                all_pii.extend(result.pii_found)
                all_categories.update(result.categories_found)
                return scrubbed
            elif isinstance(value, dict):
                return {k: await scrub_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [await scrub_value(item) for item in value]
            else:
                return value
        
        scrubbed_event = await scrub_value(event)
        
        return scrubbed_event, ScrubResult(
            original_length=original_len,
            scrubbed_length=scrubbed_len,
            pii_found=all_pii,
            pii_count=len(all_pii),
            categories_found=all_categories,
        )
    
    def scrub_event_sync(self, event: dict[str, Any]) -> tuple[dict[str, Any], ScrubResult]:
        """Synchronous version of scrub_event."""
        return asyncio.get_event_loop().run_until_complete(self.scrub_event(event))
    
    async def scrub_batch_text(self, texts: list[str]) -> list[tuple[str, ScrubResult]]:
        """Scrub multiple texts concurrently."""
        tasks = [self.scrub_text(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def scrub_batch_images(self, image_paths: list[Path]) -> list[ImageScrubResult]:
        """Scrub multiple images concurrently."""
        tasks = [self.scrub_image(path) for path in image_paths]
        return await asyncio.gather(*tasks)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the scrubber configuration."""
        return {
            "enabled": self.config.enabled,
            "level": self.config.level.value,
            "pattern_count": len(self._matcher.patterns),
            "allow_list_count": len(self.config.allow_list),
            "disabled_types": list(self.config.disabled_types),
            "scrub_text": self.config.scrub_text,
            "scrub_images": self.config.scrub_images,
            "scrub_events": self.config.scrub_events,
        }


class CapturePrivacyHook:
    """
    Hook for integrating privacy scrubbing with the capture module.
    
    Can be attached to the Recorder to automatically scrub events.
    """
    
    def __init__(self, scrubber: PrivacyScrubber):
        self.scrubber = scrubber
        self._stats = {
            "events_processed": 0,
            "pii_instances_found": 0,
            "images_scrubbed": 0,
        }
    
    async def on_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Process an event through the privacy scrubber."""
        scrubbed, result = await self.scrubber.scrub_event(event)
        self._stats["events_processed"] += 1
        self._stats["pii_instances_found"] += result.pii_count
        return scrubbed
    
    async def on_screenshot(self, screenshot_path: Path) -> Path:
        """Process a screenshot through the privacy scrubber."""
        result = await self.scrubber.scrub_image(screenshot_path)
        self._stats["images_scrubbed"] += 1
        return result.scrubbed_path
    
    def get_stats(self) -> dict[str, int]:
        """Get processing statistics."""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._stats = {
            "events_processed": 0,
            "pii_instances_found": 0,
            "images_scrubbed": 0,
        }


__all__ = [
    "ScrubLevel",
    "PrivacyConfig",
    "ScrubResult",
    "ImageScrubResult",
    "PrivacyScrubber",
    "CapturePrivacyHook",
    "PIICategory",
    "PIIType",
    "PIIPattern",
    "PatternConfig",
    "PatternMatcher",
    "AllowListEntry",
    "get_default_patterns",
    "get_patterns_by_level",
]
