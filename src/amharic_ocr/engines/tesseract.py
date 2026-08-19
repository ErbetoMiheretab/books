"""
Tesseract OCR Engine with focused Amharic Fidel & Ethiopic Numeral recognition.
Implements multi-PSM passes, character whitelisting, and fallback strategies from amh_ocr_nums.py.
"""


import numpy as np
import pytesseract
from PIL import Image

from ..constants import ALL_ETHIOPIC_NUMERALS, AMHARIC_FIDEL, LATIN_CHARS
from ..preprocessing.image_prep import preprocess_for_numerals, preprocess_for_text
from .base import OCREngine, OCRResult


class TesseractEngine(OCREngine):
    def __init__(self):
        try:
            self.available_langs = pytesseract.get_languages()
        except Exception:  # noqa: BLE001
            self.available_langs = []

    def _get_confidence(self, pil_img: Image.Image, lang: str, config_str: str) -> float:
        """Calculate mean confidence for recognized words."""
        try:
            data = pytesseract.image_to_data(pil_img, lang=lang, config=config_str, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data['conf'] if c != -1 and c != '-1']
            if confidences:
                return float(np.mean(confidences)) / 100.0
            return 0.0
        except Exception:  # noqa: BLE001
            return -1.0

    def ocr_with_whitelist(
        self, 
        image: np.ndarray, 
        whitelist: str | None = None, 
        lang: str = "amh", 
        psm: int = 6, 
        oem: int = 3
    ) -> OCRResult:
        """
        Run OCR with a specific character whitelist and PSM.
        
        Args:
            image: Preprocessed OpenCV image (numpy array)
            whitelist: String of allowed characters
            lang: Language code ('amh', 'amh+eng', etc.)
            psm: Page Segmentation Mode
            oem: OCR Engine Mode (3 = default)
        """
        pil_img = Image.fromarray(image)
        
        # Build configuration
        config_str = f'--psm {psm} --oem {oem}'
        if whitelist:
            # Escape special regex characters in whitelist
            escaped_wl = whitelist.replace('\\', '\\\\').replace('-', '\\-')
            config_str += f' -c tessedit_char_whitelist={escaped_wl}'
            
        try:
            text = pytesseract.image_to_string(pil_img, lang=lang, config=config_str).strip()
            confidence = self._get_confidence(pil_img, lang, config_str)
            return OCRResult(
                text=text,
                confidence=confidence,
                engine_name=f"tesseract_{lang}_psm{psm}",
                metadata={"psm": psm, "oem": oem, "lang": lang, "has_whitelist": bool(whitelist)}
            )
        except Exception as e:  # noqa: BLE001
            return OCRResult(
                text=f"[Tesseract Error: {e}]",
                confidence=0.0,
                engine_name="tesseract_error",
                metadata={"error": str(e)}
            )

    def ocr_numerals_only(self, image: np.ndarray) -> OCRResult:
        """
        OCR focused only on Ethiopic numerals.
        Applies gentle numeral preprocessing and tests PSM 10, 7, and 8.
        """
        whitelist = ALL_ETHIOPIC_NUMERALS
        processed = preprocess_for_numerals(image)
        
        results: list[OCRResult] = []
        
        # PSM 10: Single character mode (good for isolated numerals)
        res10 = self.ocr_with_whitelist(processed, whitelist=whitelist, lang="amh", psm=10)
        results.append(res10)
        
        # PSM 7: Single text line
        res7 = self.ocr_with_whitelist(processed, whitelist=whitelist, lang="amh", psm=7)
        results.append(res7)
        
        # PSM 8: Single word
        res8 = self.ocr_with_whitelist(processed, whitelist=whitelist, lang="amh", psm=8)
        results.append(res8)
        
        # Select best result (longest non-empty valid string)
        valid_results = [r for r in results if r.text and not r.text.startswith("[Tesseract Error")]
        if valid_results:
            return max(valid_results, key=lambda r: len(r.text))
        return results[0] if results else OCRResult(text="", confidence=0.0, engine_name="tesseract_numerals")

    def ocr_mixed_content(self, image: np.ndarray, lang: str = "amh+eng", psm: int = 6) -> OCRResult:
        """
        OCR for mixed Amharic text and numerals using combined whitelist.
        """
        whitelist = AMHARIC_FIDEL + ALL_ETHIOPIC_NUMERALS + LATIN_CHARS
        processed = preprocess_for_text(image)
        
        # Check language availability
        if 'amh' not in self.available_langs:
            lang = "eng"
            
        return self.ocr_with_whitelist(processed, whitelist=whitelist, lang=lang, psm=psm)

    def ocr_with_fallback(self, image: np.ndarray, config=None) -> OCRResult:
        """
        Try multiple OCR approaches and combine results as designed in amh_ocr_nums.py:
        1. Approach 1: Mixed content with whitelist (amh+eng, psm=6)
        2. Approach 2: Numeral-focused (multi-PSM numeral whitelist)
        3. Approach 3: Standard amh+eng with no whitelist
        """
        results: list[OCRResult] = []
        
        # Determine language preference
        lang_str = "+".join(config.languages) if config and hasattr(config, 'languages') else "amh+eng"
        psm_val = config.tesseract_psm if config and hasattr(config, 'tesseract_psm') else 6
        
        # Approach 1: Mixed content with whitelist
        try:
            res1 = self.ocr_mixed_content(image, lang=lang_str, psm=psm_val)
            if res1.text and not res1.text.startswith("[Tesseract Error"):
                results.append(res1)
        except Exception:  # noqa: BLE001, S110
            pass
            
        # Approach 2: Numeral-focused
        try:
            res2 = self.ocr_numerals_only(image)
            if res2.text and not res2.text.startswith("[Tesseract Error"):
                results.append(res2)
        except Exception:  # noqa: BLE001, S110
            pass
            
        # Approach 3: Standard without whitelist
        try:
            processed = preprocess_for_text(image)
            res3 = self.ocr_with_whitelist(processed, whitelist=None, lang=lang_str, psm=psm_val)
            if res3.text and not res3.text.startswith("[Tesseract Error"):
                results.append(res3)
        except Exception:  # noqa: BLE001, S110
            pass
            
        if results:
            # Pick longest valid text result
            return max(results, key=lambda r: len(r.text))
            
        return OCRResult(text="", confidence=0.0, engine_name="tesseract_fallback")

    def recognize(self, image: np.ndarray, config=None) -> OCRResult:
        """
        Primary engine interface. Executes multi-approach fallback recognition.
        """
        return self.ocr_with_fallback(image, config=config)
