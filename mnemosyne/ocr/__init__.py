"""OCR text extraction from screenshots."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


@dataclass
class OCRResult:
    text: str
    confidence: float
    source_path: str
    timestamp: float | None = None
    bounds: dict[str, int] | None = None


class OCRExtractor:
    
    def __init__(self, language: str = "eng"):
        self.language = language
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        if not HAS_PIL:
            raise ImportError(
                "PIL is required for OCR. Install with: pip install Pillow"
            )
    
    def extract_text(self, image_path: str | Path) -> OCRResult:
        path = Path(image_path)
        
        if not path.exists():
            return OCRResult(
                text="",
                confidence=0.0,
                source_path=str(path),
            )
        
        if HAS_TESSERACT:
            return self._extract_with_tesseract(path)
        else:
            return self._extract_with_vision_api(path)
    
    def _extract_with_tesseract(self, path: Path) -> OCRResult:
        try:
            image = Image.open(path)
            
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT,
            )
            
            texts = []
            confidences = []
            
            for i, text in enumerate(data["text"]):
                conf = float(data["conf"][i])
                if conf > 0 and text.strip():
                    texts.append(text)
                    confidences.append(conf)
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence / 100.0,
                source_path=str(path),
            )
            
        except Exception as e:
            return OCRResult(
                text=f"OCR failed: {e}",
                confidence=0.0,
                source_path=str(path),
            )
    
    def _extract_with_vision_api(self, path: Path) -> OCRResult:
        try:
            import subprocess
            
            result = subprocess.run(
                [
                    "shortcuts", "run", "Extract Text from Image",
                    "-i", str(path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 0:
                return OCRResult(
                    text=result.stdout.strip(),
                    confidence=0.8,
                    source_path=str(path),
                )
            
        except Exception:
            pass
        
        return OCRResult(
            text="",
            confidence=0.0,
            source_path=str(path),
        )
    
    def extract_from_multiple(self, image_paths: list[str | Path]) -> list[OCRResult]:
        results = []
        for path in image_paths:
            results.append(self.extract_text(path))
        return results
    
    def search_in_screenshots(
        self,
        screenshot_dir: Path,
        query: str,
        limit: int = 20,
    ) -> list[tuple[OCRResult, float]]:
        if not screenshot_dir.exists():
            return []
        
        screenshots = sorted(
            screenshot_dir.glob("*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit * 2]
        
        results = []
        query_lower = query.lower()
        
        for path in screenshots:
            ocr_result = self.extract_text(path)
            
            if query_lower in ocr_result.text.lower():
                relevance = ocr_result.text.lower().count(query_lower)
                results.append((ocr_result, relevance))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


class ScreenshotIndexer:
    
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path.home() / ".mnemosyne"
        self.screenshots_dir = self.data_dir / "screenshots"
        self.index_path = self.data_dir / "ocr_index.json"
        self.ocr = OCRExtractor()
        self._index: dict[str, OCRResult] = {}
    
    def index_screenshot(self, path: Path, timestamp: float | None = None) -> OCRResult:
        result = self.ocr.extract_text(path)
        result.timestamp = timestamp or path.stat().st_mtime
        
        self._index[str(path)] = result
        return result
    
    def index_all(self, force: bool = False) -> int:
        if not self.screenshots_dir.exists():
            return 0
        
        self._load_index()
        
        indexed = 0
        for path in self.screenshots_dir.glob("*.png"):
            path_str = str(path)
            
            if not force and path_str in self._index:
                continue
            
            self.index_screenshot(path)
            indexed += 1
        
        self._save_index()
        return indexed
    
    def search(self, query: str, limit: int = 20) -> list[OCRResult]:
        self._load_index()
        
        query_lower = query.lower()
        results = []
        
        for result in self._index.values():
            if query_lower in result.text.lower():
                results.append(result)
        
        results.sort(key=lambda r: r.timestamp or 0, reverse=True)
        return results[:limit]
    
    def _load_index(self) -> None:
        import json
        
        if not self.index_path.exists():
            return
        
        try:
            with open(self.index_path) as f:
                data = json.load(f)
            
            self._index = {
                path: OCRResult(
                    text=item["text"],
                    confidence=item["confidence"],
                    source_path=item["source_path"],
                    timestamp=item.get("timestamp"),
                )
                for path, item in data.items()
            }
        except Exception:
            self._index = {}
    
    def _save_index(self) -> None:
        import json
        
        data = {
            path: {
                "text": result.text,
                "confidence": result.confidence,
                "source_path": result.source_path,
                "timestamp": result.timestamp,
            }
            for path, result in self._index.items()
        }
        
        with open(self.index_path, "w") as f:
            json.dump(data, f)
