"""Screen capture for macOS using native APIs."""

import io
import time
from pathlib import Path
from typing import Callable
import asyncio

from PIL import Image


class ScreenCapture:
    """Captures screenshots using macOS native APIs."""
    
    def __init__(
        self,
        output_dir: Path,
        quality: int = 80,
        format: str = "webp",
    ):
        """
        Initialize screen capture.
        
        Args:
            output_dir: Directory to save screenshots
            quality: Image quality (1-100)
            format: Image format (webp, png, jpeg)
        """
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.format = format
        self._capture_count = 0
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def capture(self) -> tuple[bytes, int, int]:
        """
        Capture the current screen.
        
        Returns:
            Tuple of (image_bytes, width, height)
        """
        try:
            # Try using native macOS API
            return self._capture_macos()
        except ImportError:
            # Fallback to PIL/pillow screenshot
            return self._capture_pil()
    
    def _capture_macos(self) -> tuple[bytes, int, int]:
        """Capture using macOS Quartz APIs."""
        from Quartz import (
            CGWindowListCreateImage,
            CGRectInfinite,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
        )
        from Quartz.CoreGraphics import (
            CGImageGetWidth,
            CGImageGetHeight,
            CGImageGetDataProvider,
            CGDataProviderCopyData,
            CGImageGetBitsPerPixel,
            CGImageGetBytesPerRow,
        )
        
        # Capture the entire screen
        image_ref = CGWindowListCreateImage(
            CGRectInfinite,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            0
        )
        
        if image_ref is None:
            raise RuntimeError("Failed to capture screen")
        
        width = CGImageGetWidth(image_ref)
        height = CGImageGetHeight(image_ref)
        
        # Convert to PIL Image
        data_provider = CGImageGetDataProvider(image_ref)
        data = CGDataProviderCopyData(data_provider)
        bytes_per_row = CGImageGetBytesPerRow(image_ref)
        
        # Create PIL image from raw data
        image = Image.frombytes(
            "RGBA",
            (width, height),
            bytes(data),
            "raw",
            "BGRA",
            bytes_per_row,
        )
        
        # Convert to RGB (remove alpha)
        image = image.convert("RGB")
        
        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format=self.format.upper(), quality=self.quality)
        
        return buffer.getvalue(), width, height
    
    def _capture_pil(self) -> tuple[bytes, int, int]:
        """Capture using PIL/pillow (fallback)."""
        try:
            from PIL import ImageGrab
        except ImportError:
            raise ImportError(
                "PIL ImageGrab not available. "
                "Install pillow with: pip install pillow"
            )
        
        image = ImageGrab.grab()
        width, height = image.size
        
        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format=self.format.upper(), quality=self.quality)
        
        return buffer.getvalue(), width, height
    
    def capture_to_file(self, filename: str | None = None) -> tuple[Path, int, int, int]:
        """
        Capture screenshot and save to file.
        
        Args:
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Tuple of (filepath, width, height, file_size)
        """
        image_bytes, width, height = self.capture()
        
        if filename is None:
            self._capture_count += 1
            timestamp = int(time.time() * 1000)
            filename = f"screenshot_{timestamp}_{self._capture_count}.{self.format}"
        
        filepath = self.output_dir / filename
        filepath.write_bytes(image_bytes)
        
        return filepath, width, height, len(image_bytes)
    
    async def capture_async(self) -> tuple[bytes, int, int]:
        """Capture screenshot asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.capture)
    
    async def capture_to_file_async(
        self, filename: str | None = None
    ) -> tuple[Path, int, int, int]:
        """Capture screenshot to file asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.capture_to_file, filename)
