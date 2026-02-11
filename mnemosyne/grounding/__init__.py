"""Visual grounding module for detecting and labeling UI elements in screenshots."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from .detection import UIElementDetector
from .models import (
    AnnotationStyle,
    BoundingBox,
    DetectionConfig,
    ElementType,
    GroundingResult,
    UIElement,
)

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

__all__ = [
    "VisualGrounder",
    "UIElement",
    "ElementType",
    "BoundingBox",
    "AnnotationStyle",
    "DetectionConfig",
    "GroundingResult",
]


class VisualGrounder:
    
    def __init__(
        self,
        detection_config: DetectionConfig | None = None,
        annotation_style: AnnotationStyle | None = None,
    ):
        self.detection_config = detection_config or DetectionConfig()
        self.annotation_style = annotation_style or AnnotationStyle()
        self._detector = UIElementDetector(self.detection_config)
    
    async def detect_elements(self, image_path: str | Path) -> list[UIElement]:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        elements, _ = self._detector.detect(path)
        return elements
    
    async def annotate_image(
        self,
        image_path: str | Path,
        elements: list[UIElement] | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        if elements is None:
            elements, _ = self._detector.detect(path)
        
        image = Image.open(path)
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", self.annotation_style.font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()
        
        for element in elements:
            self._draw_element_marker(draw, element, font)
        
        annotated = Image.alpha_composite(image, overlay)
        annotated = annotated.convert("RGB")
        
        if output_path is None:
            output_path = path.parent / f"{path.stem}_annotated{path.suffix}"
        else:
            output_path = Path(output_path)
        
        annotated.save(output_path)
        return output_path
    
    def _draw_element_marker(
        self,
        draw: ImageDraw.ImageDraw,
        element: UIElement,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> None:
        style = self.annotation_style
        cx, cy = element.center
        radius = style.marker_radius
        
        marker_color = style.get_marker_color(element.element_type)
        
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(*marker_color, 220),
            outline=(*style.marker_outline_color, 255),
            width=style.marker_outline_width,
        )
        
        label = element.label
        try:
            bbox = font.getbbox(label)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width = len(label) * 6
            text_height = 10
        
        text_x = cx - text_width // 2
        text_y = cy - text_height // 2
        
        draw.text(
            (text_x, text_y),
            label,
            fill=(*style.font_color, 255),
            font=font,
        )
        
        if style.show_bounds:
            bounds = element.bounds
            draw.rectangle(
                [bounds.x, bounds.y, bounds.right, bounds.bottom],
                outline=(*style.bounds_color, 200),
                width=style.bounds_width,
            )
    
    def get_element_at_point(
        self,
        x: int,
        y: int,
        elements: list[UIElement],
    ) -> UIElement | None:
        candidates = [e for e in elements if e.contains_point(x, y)]
        if not candidates:
            return None
        return min(candidates, key=lambda e: e.bounds.area)
    
    async def generate_som_prompt(
        self,
        image_path: str | Path,
        elements: list[UIElement] | None = None,
    ) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        if elements is None:
            elements, _ = self._detector.detect(path)
        
        image = Image.open(path)
        width, height = image.size
        
        lines = [
            f"Screenshot ({width}x{height}) with {len(elements)} detected UI elements:",
            "",
        ]
        
        interactive = [e for e in elements if e.is_interactive]
        non_interactive = [e for e in elements if not e.is_interactive]
        
        if interactive:
            lines.append("Interactive elements:")
            for element in interactive:
                cx, cy = element.center
                lines.append(
                    f"  [{element.id}] {element.element_type.value} at ({cx}, {cy}) "
                    f"- {element.bounds.width}x{element.bounds.height}px"
                )
            lines.append("")
        
        if non_interactive:
            lines.append("Other elements:")
            for element in non_interactive:
                cx, cy = element.center
                lines.append(
                    f"  [{element.id}] {element.element_type.value} at ({cx}, {cy})"
                )
            lines.append("")
        
        lines.extend([
            "To interact with an element, specify its number.",
            "Example: 'Click element 3' or 'Type in element 5'",
        ])
        
        return "\n".join(lines)
    
    async def ground_image(
        self,
        image_path: str | Path,
        output_path: str | Path | None = None,
    ) -> GroundingResult:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        elements, processing_time = self._detector.detect(path)
        
        image = Image.open(path)
        width, height = image.size
        
        annotated_path = await self.annotate_image(path, elements, output_path)
        
        return GroundingResult(
            source_path=str(path),
            annotated_path=str(annotated_path),
            elements=elements,
            image_width=width,
            image_height=height,
            processing_time_ms=processing_time,
        )
