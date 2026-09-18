
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


class OCRResultCombiner:
    @staticmethod
    def combine(results: list[OCRResult], strategy: str = "confidence") -> OCRResult:
        """
        Combine OCR results from multiple engines.
        
        Supported strategies:
        - "confidence": Selects result with highest confidence (default)
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
            # "confidence" (default): confidence first, then Ethiopic density
            # as a tiebreaker, then length.  Ethiopic density rewards results
            # that contain actual Fidel characters over Latin-garbage outputs
            # at similar confidence levels.
            return max(valid_results, key=lambda r: (r.confidence, _ethiopic_ratio(r.text), len(r.text)))

