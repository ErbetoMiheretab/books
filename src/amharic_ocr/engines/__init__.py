from .base import OCREngine, OCRResult
from .tesseract import TesseractEngine

try:
    from .easyocr_engine import EasyOCREngine
except ImportError:
    # Fallback placeholder if easyocr isn't installed
    class EasyOCREngine(OCREngine):  # type: ignore
        def recognize(self, image, config) -> OCRResult:
            return OCRResult(text="[EasyOCR is not installed]", confidence=0.0, engine_name="easyocr")

__all__ = ["OCREngine", "OCRResult", "TesseractEngine", "EasyOCREngine"]
