"""Tests for grounding module - UI element detection and classification."""

import pytest

from mnemosyne.grounding.models import (
    BoundingBox,
    UIElement,
    ElementType,
    AnnotationStyle,
    DetectionConfig,
    GroundingResult,
)


class TestBoundingBox:

    def test_create_bounding_box(self):
        box = BoundingBox(x=10, y=20, width=100, height=50)
        assert box.x == 10
        assert box.y == 20
        assert box.width == 100
        assert box.height == 50

    def test_center_property(self):
        box = BoundingBox(x=0, y=0, width=100, height=100)
        assert box.center == (50, 50)

    def test_center_with_offset(self):
        box = BoundingBox(x=10, y=20, width=100, height=50)
        assert box.center == (60, 45)

    def test_area_property(self):
        box = BoundingBox(x=0, y=0, width=100, height=50)
        assert box.area == 5000

    def test_right_property(self):
        box = BoundingBox(x=10, y=0, width=100, height=50)
        assert box.right == 110

    def test_bottom_property(self):
        box = BoundingBox(x=0, y=20, width=100, height=50)
        assert box.bottom == 70

    def test_contains_point_inside(self):
        box = BoundingBox(x=0, y=0, width=100, height=100)
        assert box.contains_point(50, 50) is True

    def test_contains_point_on_edge(self):
        box = BoundingBox(x=0, y=0, width=100, height=100)
        assert box.contains_point(0, 0) is True
        assert box.contains_point(100, 100) is True

    def test_contains_point_outside(self):
        box = BoundingBox(x=0, y=0, width=100, height=100)
        assert box.contains_point(150, 50) is False
        assert box.contains_point(50, 150) is False
        assert box.contains_point(-10, 50) is False

    def test_intersects_overlapping(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=50, y=50, width=100, height=100)
        assert box1.intersects(box2) is True
        assert box2.intersects(box1) is True

    def test_intersects_non_overlapping(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=200, y=200, width=100, height=100)
        assert box1.intersects(box2) is False

    def test_intersects_adjacent(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=100, y=0, width=100, height=100)
        assert box1.intersects(box2) is True

    def test_intersection_area_overlapping(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=50, y=50, width=100, height=100)
        assert box1.intersection_area(box2) == 2500

    def test_intersection_area_non_overlapping(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=200, y=200, width=100, height=100)
        assert box1.intersection_area(box2) == 0

    def test_intersection_area_contained(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=25, y=25, width=50, height=50)
        assert box1.intersection_area(box2) == 2500


class TestUIElement:

    def test_create_element(self):
        bounds = BoundingBox(x=10, y=20, width=100, height=50)
        element = UIElement(
            id=1,
            element_type=ElementType.BUTTON,
            bounds=bounds,
            confidence=0.9,
            label="Submit",
        )
        assert element.id == 1
        assert element.element_type == ElementType.BUTTON
        assert element.confidence == 0.9
        assert element.label == "Submit"

    def test_element_center(self):
        bounds = BoundingBox(x=0, y=0, width=100, height=100)
        element = UIElement(id=1, bounds=bounds)
        assert element.center == (50, 50)

    def test_element_contains_point(self):
        bounds = BoundingBox(x=0, y=0, width=100, height=100)
        element = UIElement(id=1, bounds=bounds)
        assert element.contains_point(50, 50) is True
        assert element.contains_point(150, 50) is False

    def test_element_default_values(self):
        bounds = BoundingBox(x=0, y=0, width=100, height=100)
        element = UIElement(id=1, bounds=bounds)
        assert element.element_type == ElementType.UNKNOWN
        assert element.confidence == 0.5
        assert element.label == ""
        assert element.is_interactive is True
        assert element.parent_id is None


class TestElementType:

    def test_element_types(self):
        assert ElementType.BUTTON == "button"
        assert ElementType.INPUT == "input"
        assert ElementType.LINK == "link"
        assert ElementType.ICON == "icon"
        assert ElementType.TEXT == "text"
        assert ElementType.IMAGE == "image"
        assert ElementType.CONTAINER == "container"
        assert ElementType.CHECKBOX == "checkbox"
        assert ElementType.DROPDOWN == "dropdown"
        assert ElementType.UNKNOWN == "unknown"

    def test_element_type_is_string(self):
        assert isinstance(ElementType.BUTTON.value, str)


class TestAnnotationStyle:

    def test_default_style(self):
        style = AnnotationStyle()
        assert style.marker_radius == 12
        assert style.marker_color == (255, 0, 0)
        assert style.font_size == 10
        assert style.show_bounds is False

    def test_custom_style(self):
        style = AnnotationStyle(
            marker_radius=20,
            marker_color=(0, 255, 0),
            show_bounds=True,
        )
        assert style.marker_radius == 20
        assert style.marker_color == (0, 255, 0)
        assert style.show_bounds is True

    def test_get_marker_color_with_type_colors(self):
        style = AnnotationStyle(use_type_colors=True)
        color = style.get_marker_color(ElementType.BUTTON)
        assert color == (255, 100, 100)

    def test_get_marker_color_without_type_colors(self):
        style = AnnotationStyle(use_type_colors=False, marker_color=(0, 0, 255))
        color = style.get_marker_color(ElementType.BUTTON)
        assert color == (0, 0, 255)

    def test_type_colors_mapping(self):
        style = AnnotationStyle()
        assert ElementType.BUTTON in style.type_colors
        assert ElementType.INPUT in style.type_colors
        assert ElementType.LINK in style.type_colors


class TestDetectionConfig:

    def test_default_config(self):
        config = DetectionConfig()
        assert config.edge_low_threshold == 50
        assert config.edge_high_threshold == 150
        assert config.min_element_area == 100
        assert config.max_element_area == 500000
        assert config.min_confidence == 0.3

    def test_custom_config(self):
        config = DetectionConfig(
            edge_low_threshold=30,
            edge_high_threshold=200,
            min_element_area=50,
        )
        assert config.edge_low_threshold == 30
        assert config.edge_high_threshold == 200
        assert config.min_element_area == 50

    def test_aspect_ratio_ranges(self):
        config = DetectionConfig()
        assert config.button_aspect_ratio_range == (0.5, 5.0)
        assert config.input_aspect_ratio_range == (2.0, 20.0)
        assert config.icon_max_size == 64


class TestGroundingResult:

    def test_create_result(self):
        result = GroundingResult(
            source_path="/path/to/image.png",
            image_width=1920,
            image_height=1080,
        )
        assert result.source_path == "/path/to/image.png"
        assert result.image_width == 1920
        assert result.image_height == 1080
        assert result.element_count == 0

    def test_element_count(self):
        bounds = BoundingBox(x=0, y=0, width=100, height=50)
        elements = [
            UIElement(id=1, bounds=bounds),
            UIElement(id=2, bounds=bounds),
            UIElement(id=3, bounds=bounds),
        ]
        result = GroundingResult(
            source_path="/path/to/image.png",
            elements=elements,
        )
        assert result.element_count == 3

    def test_get_element_by_id(self):
        bounds = BoundingBox(x=0, y=0, width=100, height=50)
        elements = [
            UIElement(id=1, bounds=bounds, label="First"),
            UIElement(id=2, bounds=bounds, label="Second"),
        ]
        result = GroundingResult(
            source_path="/path/to/image.png",
            elements=elements,
        )
        
        element = result.get_element_by_id(1)
        assert element is not None
        assert element.label == "First"
        
        element = result.get_element_by_id(99)
        assert element is None

    def test_get_element_at_point(self):
        elements = [
            UIElement(id=1, bounds=BoundingBox(x=0, y=0, width=200, height=200)),
            UIElement(id=2, bounds=BoundingBox(x=50, y=50, width=50, height=50)),
        ]
        result = GroundingResult(
            source_path="/path/to/image.png",
            elements=elements,
        )
        
        element = result.get_element_at_point(75, 75)
        assert element is not None
        assert element.id == 2

    def test_get_element_at_point_no_match(self):
        elements = [
            UIElement(id=1, bounds=BoundingBox(x=0, y=0, width=100, height=100)),
        ]
        result = GroundingResult(
            source_path="/path/to/image.png",
            elements=elements,
        )
        
        element = result.get_element_at_point(500, 500)
        assert element is None

    def test_get_elements_by_type(self):
        elements = [
            UIElement(id=1, bounds=BoundingBox(x=0, y=0, width=100, height=50), element_type=ElementType.BUTTON),
            UIElement(id=2, bounds=BoundingBox(x=0, y=0, width=100, height=50), element_type=ElementType.INPUT),
            UIElement(id=3, bounds=BoundingBox(x=0, y=0, width=100, height=50), element_type=ElementType.BUTTON),
        ]
        result = GroundingResult(
            source_path="/path/to/image.png",
            elements=elements,
        )
        
        buttons = result.get_elements_by_type(ElementType.BUTTON)
        assert len(buttons) == 2
        
        inputs = result.get_elements_by_type(ElementType.INPUT)
        assert len(inputs) == 1
        
        links = result.get_elements_by_type(ElementType.LINK)
        assert len(links) == 0


class TestElementClassification:

    def test_classify_by_aspect_ratio_button(self):
        config = DetectionConfig(button_aspect_ratio_range=(0.5, 5.0))
        assert 0.5 <= 2.0 <= 5.0

    def test_classify_by_aspect_ratio_input(self):
        config = DetectionConfig(input_aspect_ratio_range=(2.0, 20.0))
        assert 2.0 <= 10.0 <= 20.0

    def test_icon_max_size(self):
        config = DetectionConfig(icon_max_size=64)
        assert 32 <= config.icon_max_size
        assert 48 <= config.icon_max_size


class TestEdgeDetectionConfig:

    def test_edge_thresholds(self):
        config = DetectionConfig(
            edge_low_threshold=30,
            edge_high_threshold=100,
        )
        assert config.edge_low_threshold < config.edge_high_threshold

    def test_merge_overlap_threshold(self):
        config = DetectionConfig(merge_overlap_threshold=0.5)
        assert 0.0 <= config.merge_overlap_threshold <= 1.0

    def test_min_max_aspect_ratio(self):
        config = DetectionConfig(
            min_aspect_ratio=0.1,
            max_aspect_ratio=10.0,
        )
        assert config.min_aspect_ratio < config.max_aspect_ratio
