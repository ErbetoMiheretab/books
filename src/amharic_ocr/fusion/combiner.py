
from ..engines.base import OCRResult


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
        elif strategy == "confidence":
            # Sort by confidence primarily, then text length
            return max(valid_results, key=lambda r: (r.confidence, len(r.text)))
        else:
            # Default fallback
            return max(valid_results, key=lambda r: (r.confidence, len(r.text)))
