"""
Amharic OCR Package with focused Ethiopic Numeral Recognition.
"""

from .config import OCRConfig
from .constants import ALL_ETHIOPIC_NUMERALS, ALLOWED_EXTRA_CHARS, AMHARIC_FIDEL, ETHIOPIC_NUMERALS, ETHIOPIC_PUNCTUATION
from .diagnostics import check_system_setup, test_numeral_recognition
from .engines.tesseract import TesseractEngine
from .pipeline import process_single_page, run_pipeline
from .postprocessing.corrections import (
    convert_digits_to_ethiopic,
    correct_common_errors,
    deduplicate_numeral_loops,
    extract_ethiopic_numerals,
    post_process_text,
)

__all__ = [
    "ALL_ETHIOPIC_NUMERALS",
    "AMHARIC_FIDEL",
    "ETHIOPIC_NUMERALS",
    "OCRConfig",
    "TesseractEngine",
    "check_system_setup",
    "convert_digits_to_ethiopic",
    "correct_common_errors",
    "deduplicate_numeral_loops",
    "extract_ethiopic_numerals",
    "post_process_text",
    "process_single_page",
    "run_pipeline",
    "test_numeral_recognition",
]
