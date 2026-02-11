"""Pydantic models for visual grounding."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ElementType(str, Enum):
    """Types of UI elements that can be detected."""
    
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    ICON = "icon"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Bounding box for a UI element."""
    
    x: int = Field(description="X coordinate of top-left corner")
    y: int = Field(description="Y coordinate of top-left corner")
    width: int = Field(description="Width of the bounding box")
    height: int = Field(description="Height of the bounding box")
    
    @property
    def center(self) -> tuple[int, int]:
        """Get center point of the bounding box."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        """Get area of the bounding box."""
        return self.width * self.height
    
    @property
    def right(self) -> int:
        """Get right edge x coordinate."""
        return self.x + self.width
    
    @property
    def bottom(self) -> int:
        """Get bottom edge y coordinate."""
        return self.y + self.height
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside this bounding box."""
        return (
            self.x <= x <= self.right
            and self.y <= y <= self.bottom
        )
    
    def intersects(self, other: "BoundingBox") -> bool:
        """Check if this bounding box intersects with another."""
        return not (
            self.right < other.x
            or other.right < self.x
            or self.bottom < other.y
            or other.bottom < self.y
        )
    
    def intersection_area(self, other: "BoundingBox") -> int:
        """Calculate intersection area with another bounding box."""
        if not self.intersects(other):
            return 0
        
        x_overlap = max(0, min(self.right, other.right) - max(self.x, other.x))
        y_overlap = max(0, min(self.bottom, other.bottom) - max(self.y, other.y))
        return x_overlap * y_overlap


class UIElement(BaseModel):
    """A detected UI element with its properties."""
    
    id: int = Field(description="Unique identifier/label number for this element")
    element_type: ElementType = Field(default=ElementType.UNKNOWN, description="Type of UI element")
    bounds: BoundingBox = Field(description="Bounding box of the element")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Detection confidence")
    label: str = Field(default="", description="Text label for the element")
    
    # Additional metadata
    is_interactive: bool = Field(default=True, description="Whether element is likely interactive")
    parent_id: int | None = Field(default=None, description="ID of parent container element")
    
    @property
    def center(self) -> tuple[int, int]:
        """Get center point of the element."""
        return self.bounds.center
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside this element."""
        return self.bounds.contains_point(x, y)


class AnnotationStyle(BaseModel):
    """Style configuration for annotating images with element markers."""
    
    # Marker appearance
    marker_radius: int = Field(default=12, description="Radius of the circular marker")
    marker_color: tuple[int, int, int] = Field(
        default=(255, 0, 0),
        description="RGB color for markers (default: red)"
    )
    marker_outline_color: tuple[int, int, int] = Field(
        default=(255, 255, 255),
        description="RGB color for marker outline (default: white)"
    )
    marker_outline_width: int = Field(default=2, description="Width of marker outline")
    
    # Label text
    font_size: int = Field(default=10, description="Font size for labels")
    font_color: tuple[int, int, int] = Field(
        default=(255, 255, 255),
        description="RGB color for label text (default: white)"
    )
    
    # Label position
    label_position: Literal["center", "top", "bottom", "left", "right"] = Field(
        default="center",
        description="Position of label relative to marker"
    )
    
    # Bounding box visualization
    show_bounds: bool = Field(default=False, description="Whether to draw bounding boxes")
    bounds_color: tuple[int, int, int] = Field(
        default=(0, 255, 0),
        description="RGB color for bounding boxes (default: green)"
    )
    bounds_width: int = Field(default=2, description="Width of bounding box lines")
    
    # Element type colors (for differentiation)
    type_colors: dict[ElementType, tuple[int, int, int]] = Field(
        default_factory=lambda: {
            ElementType.BUTTON: (255, 100, 100),    # Light red
            ElementType.INPUT: (100, 100, 255),     # Light blue
            ElementType.LINK: (100, 255, 100),      # Light green
            ElementType.ICON: (255, 255, 100),      # Yellow
            ElementType.TEXT: (200, 200, 200),      # Light gray
            ElementType.IMAGE: (255, 100, 255),     # Magenta
            ElementType.CONTAINER: (100, 255, 255), # Cyan
            ElementType.CHECKBOX: (255, 165, 0),    # Orange
            ElementType.DROPDOWN: (148, 0, 211),    # Violet
            ElementType.UNKNOWN: (128, 128, 128),   # Gray
        },
        description="Color mapping for different element types"
    )
    
    use_type_colors: bool = Field(
        default=True,
        description="Whether to use different colors for different element types"
    )
    
    def get_marker_color(self, element_type: ElementType) -> tuple[int, int, int]:
        """Get the marker color for a given element type."""
        if self.use_type_colors:
            return self.type_colors.get(element_type, self.marker_color)
        return self.marker_color


class DetectionConfig(BaseModel):
    """Configuration for element detection."""
    
    # Edge detection parameters
    edge_low_threshold: int = Field(default=50, description="Low threshold for Canny edge detection")
    edge_high_threshold: int = Field(default=150, description="High threshold for Canny edge detection")
    
    # Contour filtering
    min_element_area: int = Field(default=100, description="Minimum area for detected elements")
    max_element_area: int = Field(default=500000, description="Maximum area for detected elements")
    min_aspect_ratio: float = Field(default=0.1, description="Minimum aspect ratio (width/height)")
    max_aspect_ratio: float = Field(default=10.0, description="Maximum aspect ratio (width/height)")
    
    # Element classification thresholds
    button_aspect_ratio_range: tuple[float, float] = Field(
        default=(0.5, 5.0),
        description="Aspect ratio range for buttons"
    )
    input_aspect_ratio_range: tuple[float, float] = Field(
        default=(2.0, 20.0),
        description="Aspect ratio range for input fields"
    )
    icon_max_size: int = Field(default=64, description="Maximum size for icons")
    
    # Merging overlapping detections
    merge_overlap_threshold: float = Field(
        default=0.5,
        description="IoU threshold for merging overlapping detections"
    )
    
    # Confidence thresholds
    min_confidence: float = Field(default=0.3, description="Minimum confidence to keep detection")


class GroundingResult(BaseModel):
    """Result of visual grounding on an image."""
    
    source_path: str = Field(description="Path to the source image")
    annotated_path: str | None = Field(default=None, description="Path to annotated image")
    elements: list[UIElement] = Field(default_factory=list, description="Detected UI elements")
    image_width: int = Field(default=0, description="Width of source image")
    image_height: int = Field(default=0, description="Height of source image")
    processing_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")
    
    @property
    def element_count(self) -> int:
        """Get number of detected elements."""
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
        # Return smallest element (most specific)
        return min(candidates, key=lambda e: e.bounds.area)
    
    def get_elements_by_type(self, element_type: ElementType) -> list[UIElement]:
        """Get all elements of a specific type."""
        return [e for e in self.elements if e.element_type == element_type]
