"""Pure Pillow-based edge detection and contour analysis for UI element detection."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .models import (
    BoundingBox,
    DetectionConfig,
    ElementType,
    UIElement,
)

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage


@dataclass
class ContourRect:
    x: int
    y: int
    width: int
    height: int
    edge_density: float = 0.0


class EdgeDetector:
    
    def __init__(self, config: DetectionConfig | None = None):
        self.config = config or DetectionConfig()
    
    def detect_edges(self, image: PILImage) -> PILImage:
        grayscale = image.convert("L")
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        enhanced = ImageOps.autocontrast(edges)
        threshold = 30
        binary = enhanced.point(lambda p: 255 if p > threshold else 0)
        return binary
    
    def detect_edges_sobel(self, image: PILImage) -> PILImage:
        grayscale = image.convert("L")
        
        sobel_x = ImageFilter.Kernel(
            size=(3, 3),
            kernel=[-1, 0, 1, -2, 0, 2, -1, 0, 1],
            scale=1,
            offset=128,
        )
        sobel_y = ImageFilter.Kernel(
            size=(3, 3),
            kernel=[-1, -2, -1, 0, 0, 0, 1, 2, 1],
            scale=1,
            offset=128,
        )
        
        edges_x = grayscale.filter(sobel_x)
        edges_y = grayscale.filter(sobel_y)
        
        combined = Image.blend(edges_x, edges_y, 0.5)
        enhanced = ImageOps.autocontrast(combined)
        threshold = 140
        binary = enhanced.point(lambda p: 255 if abs(p - 128) > (threshold - 128) else 0)
        return binary


class ContourAnalyzer:
    
    def __init__(self, config: DetectionConfig | None = None):
        self.config = config or DetectionConfig()
    
    def find_contours(self, edge_image: PILImage) -> list[ContourRect]:
        width, height = edge_image.size
        pixels = edge_image.load()
        visited = [[False] * height for _ in range(width)]
        contours: list[ContourRect] = []
        
        for y in range(0, height, 4):
            for x in range(0, width, 4):
                if visited[x][y]:
                    continue
                if pixels[x, y] > 128:
                    rect = self._flood_fill_rect(pixels, visited, x, y, width, height)
                    if rect and self._is_valid_rect(rect):
                        contours.append(rect)
        
        return contours
    
    def _flood_fill_rect(
        self,
        pixels,
        visited: list[list[bool]],
        start_x: int,
        start_y: int,
        img_width: int,
        img_height: int,
    ) -> ContourRect | None:
        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        edge_count = 0
        total_count = 0
        
        stack = [(start_x, start_y)]
        
        while stack and total_count < 10000:
            x, y = stack.pop()
            
            if x < 0 or x >= img_width or y < 0 or y >= img_height:
                continue
            if visited[x][y]:
                continue
            
            visited[x][y] = True
            total_count += 1
            
            if pixels[x, y] > 128:
                edge_count += 1
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                
                for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < img_width and 0 <= ny < img_height and not visited[nx][ny]:
                        stack.append((nx, ny))
        
        if edge_count < 10:
            return None
        
        rect_width = max_x - min_x + 1
        rect_height = max_y - min_y + 1
        area = rect_width * rect_height
        edge_density = edge_count / area if area > 0 else 0
        
        return ContourRect(
            x=min_x,
            y=min_y,
            width=rect_width,
            height=rect_height,
            edge_density=edge_density,
        )
    
    def _is_valid_rect(self, rect: ContourRect) -> bool:
        area = rect.width * rect.height
        if area < self.config.min_element_area or area > self.config.max_element_area:
            return False
        
        aspect_ratio = rect.width / rect.height if rect.height > 0 else 0
        if aspect_ratio < self.config.min_aspect_ratio or aspect_ratio > self.config.max_aspect_ratio:
            return False
        
        return True
    
    def find_rectangular_regions(self, image: PILImage) -> list[ContourRect]:
        grayscale = image.convert("L")
        width, height = grayscale.size
        pixels = grayscale.load()
        
        regions: list[ContourRect] = []
        
        horizontal_edges = self._detect_horizontal_edges(pixels, width, height)
        vertical_edges = self._detect_vertical_edges(pixels, width, height)
        
        for h_edge in horizontal_edges:
            for v_edge in vertical_edges:
                rect = self._try_form_rectangle(h_edge, v_edge, horizontal_edges, vertical_edges)
                if rect and self._is_valid_rect(rect):
                    regions.append(rect)
        
        return self._merge_overlapping(regions)
    
    def _detect_horizontal_edges(
        self, pixels, width: int, height: int
    ) -> list[tuple[int, int, int]]:
        edges = []
        threshold = 30
        min_length = 20
        
        for y in range(1, height - 1, 3):
            start_x = None
            for x in range(width):
                diff = abs(int(pixels[x, y]) - int(pixels[x, y - 1]))
                if diff > threshold:
                    if start_x is None:
                        start_x = x
                else:
                    if start_x is not None and x - start_x >= min_length:
                        edges.append((start_x, y, x - start_x))
                    start_x = None
            
            if start_x is not None and width - start_x >= min_length:
                edges.append((start_x, y, width - start_x))
        
        return edges
    
    def _detect_vertical_edges(
        self, pixels, width: int, height: int
    ) -> list[tuple[int, int, int]]:
        edges = []
        threshold = 30
        min_length = 20
        
        for x in range(1, width - 1, 3):
            start_y = None
            for y in range(height):
                diff = abs(int(pixels[x, y]) - int(pixels[x - 1, y]))
                if diff > threshold:
                    if start_y is None:
                        start_y = y
                else:
                    if start_y is not None and y - start_y >= min_length:
                        edges.append((x, start_y, y - start_y))
                    start_y = None
            
            if start_y is not None and height - start_y >= min_length:
                edges.append((x, start_y, height - start_y))
        
        return edges
    
    def _try_form_rectangle(
        self,
        h_edge: tuple[int, int, int],
        v_edge: tuple[int, int, int],
        h_edges: list[tuple[int, int, int]],
        v_edges: list[tuple[int, int, int]],
    ) -> ContourRect | None:
        hx, hy, hw = h_edge
        vx, vy, vh = v_edge
        
        tolerance = 10
        if not (hx - tolerance <= vx <= hx + hw + tolerance and vy - tolerance <= hy <= vy + vh + tolerance):
            return None
        
        rect_x = min(hx, vx)
        rect_y = min(hy, vy)
        rect_w = max(hx + hw, vx) - rect_x
        rect_h = max(hy, vy + vh) - rect_y
        
        if rect_w < 20 or rect_h < 10:
            return None
        
        return ContourRect(x=rect_x, y=rect_y, width=rect_w, height=rect_h)
    
    def _merge_overlapping(self, rects: list[ContourRect]) -> list[ContourRect]:
        if not rects:
            return []
        
        merged: list[ContourRect] = []
        used = [False] * len(rects)
        
        for i, rect in enumerate(rects):
            if used[i]:
                continue
            
            current = rect
            used[i] = True
            
            changed = True
            while changed:
                changed = False
                for j, other in enumerate(rects):
                    if used[j]:
                        continue
                    
                    if self._should_merge(current, other):
                        current = self._merge_rects(current, other)
                        used[j] = True
                        changed = True
            
            merged.append(current)
        
        return merged
    
    def _should_merge(self, r1: ContourRect, r2: ContourRect) -> bool:
        x_overlap = max(0, min(r1.x + r1.width, r2.x + r2.width) - max(r1.x, r2.x))
        y_overlap = max(0, min(r1.y + r1.height, r2.y + r2.height) - max(r1.y, r2.y))
        intersection = x_overlap * y_overlap
        
        area1 = r1.width * r1.height
        area2 = r2.width * r2.height
        union = area1 + area2 - intersection
        
        iou = intersection / union if union > 0 else 0
        return iou > self.config.merge_overlap_threshold
    
    def _merge_rects(self, r1: ContourRect, r2: ContourRect) -> ContourRect:
        x = min(r1.x, r2.x)
        y = min(r1.y, r2.y)
        right = max(r1.x + r1.width, r2.x + r2.width)
        bottom = max(r1.y + r1.height, r2.y + r2.height)
        return ContourRect(x=x, y=y, width=right - x, height=bottom - y)


class ElementClassifier:
    
    def __init__(self, config: DetectionConfig | None = None):
        self.config = config or DetectionConfig()
    
    def classify(
        self,
        rect: ContourRect,
        image: PILImage,
    ) -> tuple[ElementType, float]:
        aspect_ratio = rect.width / rect.height if rect.height > 0 else 1.0
        area = rect.width * rect.height
        
        region = image.crop((rect.x, rect.y, rect.x + rect.width, rect.y + rect.height))
        avg_color = self._get_average_color(region)
        color_variance = self._get_color_variance(region)
        
        if rect.width <= self.config.icon_max_size and rect.height <= self.config.icon_max_size:
            if 0.7 <= aspect_ratio <= 1.4:
                return ElementType.ICON, 0.7
        
        btn_min, btn_max = self.config.button_aspect_ratio_range
        if btn_min <= aspect_ratio <= btn_max:
            if 500 <= area <= 50000:
                if color_variance < 5000:
                    return ElementType.BUTTON, 0.8
        
        inp_min, inp_max = self.config.input_aspect_ratio_range
        if inp_min <= aspect_ratio <= inp_max:
            if rect.height >= 20 and rect.height <= 60:
                if self._is_light_background(avg_color):
                    return ElementType.INPUT, 0.75
        
        if aspect_ratio > 3.0 and rect.height < 30:
            return ElementType.TEXT, 0.5
        
        if area > 10000 and color_variance > 10000:
            return ElementType.IMAGE, 0.6
        
        if area > 50000:
            return ElementType.CONTAINER, 0.4
        
        if 0.8 <= aspect_ratio <= 1.2 and rect.width < 30:
            return ElementType.CHECKBOX, 0.6
        
        return ElementType.UNKNOWN, 0.3
    
    def _get_average_color(self, region: PILImage) -> tuple[float, float, float]:
        if region.mode != "RGB":
            region = region.convert("RGB")
        
        pixels = list(region.getdata())
        if not pixels:
            return (128.0, 128.0, 128.0)
        
        r_sum = sum(p[0] for p in pixels)
        g_sum = sum(p[1] for p in pixels)
        b_sum = sum(p[2] for p in pixels)
        n = len(pixels)
        
        return (r_sum / n, g_sum / n, b_sum / n)
    
    def _get_color_variance(self, region: PILImage) -> float:
        if region.mode != "RGB":
            region = region.convert("RGB")
        
        pixels = list(region.getdata())
        if len(pixels) < 2:
            return 0.0
        
        avg = self._get_average_color(region)
        variance = sum(
            (p[0] - avg[0]) ** 2 + (p[1] - avg[1]) ** 2 + (p[2] - avg[2]) ** 2
            for p in pixels
        ) / len(pixels)
        
        return variance
    
    def _is_light_background(self, color: tuple[float, float, float]) -> bool:
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        return luminance > 200


class UIElementDetector:
    
    def __init__(self, config: DetectionConfig | None = None):
        self.config = config or DetectionConfig()
        self.edge_detector = EdgeDetector(config)
        self.contour_analyzer = ContourAnalyzer(config)
        self.classifier = ElementClassifier(config)
    
    def detect(self, image_path: str | Path) -> tuple[list[UIElement], float]:
        start_time = time.time()
        
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        edges = self.edge_detector.detect_edges(image)
        contours = self.contour_analyzer.find_contours(edges)
        rect_regions = self.contour_analyzer.find_rectangular_regions(image)
        
        all_rects = contours + rect_regions
        merged_rects = self.contour_analyzer._merge_overlapping(all_rects)
        
        elements: list[UIElement] = []
        for idx, rect in enumerate(merged_rects, start=1):
            element_type, confidence = self.classifier.classify(rect, image)
            
            if confidence < self.config.min_confidence:
                continue
            
            element = UIElement(
                id=idx,
                element_type=element_type,
                bounds=BoundingBox(
                    x=rect.x,
                    y=rect.y,
                    width=rect.width,
                    height=rect.height,
                ),
                confidence=confidence,
                label=str(idx),
                is_interactive=element_type in {
                    ElementType.BUTTON,
                    ElementType.INPUT,
                    ElementType.LINK,
                    ElementType.CHECKBOX,
                    ElementType.DROPDOWN,
                    ElementType.ICON,
                },
            )
            elements.append(element)
        
        elements = self._assign_parent_relationships(elements)
        elements = self._renumber_elements(elements)
        
        processing_time = (time.time() - start_time) * 1000
        return elements, processing_time
    
    def _assign_parent_relationships(self, elements: list[UIElement]) -> list[UIElement]:
        sorted_by_area = sorted(elements, key=lambda e: e.bounds.area, reverse=True)
        
        for i, element in enumerate(sorted_by_area):
            for potential_parent in sorted_by_area[:i]:
                if (
                    potential_parent.bounds.x <= element.bounds.x
                    and potential_parent.bounds.y <= element.bounds.y
                    and potential_parent.bounds.right >= element.bounds.right
                    and potential_parent.bounds.bottom >= element.bounds.bottom
                    and potential_parent.id != element.id
                ):
                    element.parent_id = potential_parent.id
                    break
        
        return sorted_by_area
    
    def _renumber_elements(self, elements: list[UIElement]) -> list[UIElement]:
        interactive = [e for e in elements if e.is_interactive]
        non_interactive = [e for e in elements if not e.is_interactive]
        
        interactive.sort(key=lambda e: (e.bounds.y, e.bounds.x))
        
        for idx, element in enumerate(interactive, start=1):
            element.id = idx
            element.label = str(idx)
        
        next_id = len(interactive) + 1
        for element in non_interactive:
            element.id = next_id
            element.label = str(next_id)
            next_id += 1
        
        return interactive + non_interactive
