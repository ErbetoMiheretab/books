
from ..engines.base import OCRResult


def _ethiopic_ratio(text: str) -> float:
    """Fraction of characters in the Ethiopic Unicode block (U+1200–U+137F).

    A higher ratio indicates the engine actually recognized Fidel script
    rather than substituting Latin look-alikes or producing ASCII garbage.
    """
    if not text:
        return 0.0
    ethiopic = sum(1 for c in text if '\u1200' <= c <= '\u137f')
    return ethiopic / len(text)


def score_ocr_result(result: OCRResult) -> float:
    """
    Computes a composite quality score for an OCR candidate.
    Combines:
    - Raw confidence (normalized 0.0-1.0)
    - Ethiopic (Fidel) character density (rewards valid Fidel script)
    - Valid text length (capped to prevent infinite loops / noise hallucination)
    - Garbage character penalty (penalizes runs of symbols like |, ~, ^, _)
    """
    text = result.text.strip()
    if not text:
        return -1.0

    conf = max(result.confidence, 0.0) if result.confidence != -1.0 else 0.5
    eth_ratio = _ethiopic_ratio(text)
    length_factor = min(len(text) / 500.0, 1.0)

    # Garbage characters often hallucinated on noisy margins or dark book spines
    garbage_chars = sum(1 for c in text if c in "|~^\\_`<>{}[]")
    garbage_ratio = garbage_chars / len(text)

    score = (conf * 0.35) + (eth_ratio * 0.45) + (length_factor * 0.20) - (garbage_ratio * 0.50)
    return score


class OCRResultCombiner:
    @staticmethod
    def combine(results: list[OCRResult], strategy: str = "confidence") -> OCRResult:
        """
        Combine OCR results from multiple engines.
        
        Supported strategies:
        - "confidence": Selects result using compound Fidel-density and confidence scoring (default)
        - "longest": Selects result with the longest text string
        """
        if not results:
            return OCRResult(text="", confidence=0.0, engine_name="combiner")
            
        # Filter out empty or error results
        valid_results = [
            r for r in results 
            if r.text.strip() and not r.text.startswith("[ERROR") and not r.text.startswith("[Tesseract Error")
        ]
        
        if not valid_results:
            # If all failed, return the first one (or whatever we have)
            return results[0]
            
        if strategy == "longest":
            return max(valid_results, key=lambda r: len(r.text))
        else:
            # Uses compound scoring (confidence + Ethiopic density + length - garbage penalty)
            return max(valid_results, key=score_ocr_result)

