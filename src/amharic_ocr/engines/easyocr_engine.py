"""
EasyOCR Engine implementation (optional fallback engine).
"""

import numpy as np

from ..preprocessing.image_prep import to_grayscale
from .base import OCREngine, OCRResult

# Global reader instance for worker processes (prevents reloading per page)
_reader_instance = None

def get_easyocr_reader(languages, gpu=False):
    global _reader_instance
    if _reader_instance is None:
        import easyocr
        # EasyOCR uses 2-letter ISO codes (e.g. 'en' for English)
        # Note: EasyOCR does not have native Amharic ('amh') models, but can read Latin numerals / symbols.
        lang_map = {
            'eng': 'en'
        }
        ocr_langs = [lang_map.get(lang, lang) for lang in languages if lang not in ('amh', 'am')]
        if not ocr_langs:
            ocr_langs = ['en']
        
        try:
            _reader_instance = easyocr.Reader(ocr_langs, gpu=gpu, verbose=False)
        except Exception:  # noqa: BLE001
            _reader_instance = easyocr.Reader(['en'], gpu=gpu, verbose=False)
    return _reader_instance

class EasyOCREngine(OCREngine):
    def recognize(self, image: np.ndarray, config) -> OCRResult:
        try:
            gray = to_grayscale(image)
            reader = get_easyocr_reader(config.languages, config.easyocr_gpu)
            
            results = reader.readtext(gray, detail=1, paragraph=True)
            
            if not results:
                return OCRResult(text="", confidence=1.0, engine_name="easyocr")
                
            text_blocks = []
            confidences = []
            
            for bbox, text, confidence in results:
                text_blocks.append(text)
                confidences.append(confidence)
                
            full_text = "\n".join(text_blocks)
            mean_confidence = float(np.mean(confidences)) if confidences else 1.0
            
            return OCRResult(
                text=full_text,
                confidence=mean_confidence,
                engine_name="easyocr",
                metadata={"num_blocks": len(results)}
            )
        except Exception as e:  # noqa: BLE001
            return OCRResult(
                text=f"[EasyOCR Error: {e}]",
                confidence=0.0,
                engine_name="easyocr"
            )
