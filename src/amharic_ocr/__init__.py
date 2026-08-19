"""
Amharic OCR Package with focused Ethiopic Numeral Recognition.
"""

from .config import OCRConfig
from .pipeline import run_pipeline, process_single_page
from .constants import ETHIOPIC_NUMERALS, ALL_ETHIOPIC_NUMERALS, AMHARIC_FIDEL
from .postprocessing.corrections import (
    post_process_text,
    extract_ethiopic_numerals,
    correct_common_errors,
    deduplicate_numeral_loops,
    convert_digits_to_ethiopic
)
from .engines.tesseract import TesseractEngine
from .diagnostics import check_system_setup, test_numeral_recognition

__all__ = [
    "OCRConfig",
    "run_pipeline",
    "process_single_page",
    "TesseractEngine",
    "ETHIOPIC_NUMERALS",
    "ALL_ETHIOPIC_NUMERALS",
    "AMHARIC_FIDEL",
    "post_process_text",
    "extract_ethiopic_numerals",
    "correct_common_errors",
    "deduplicate_numeral_loops",
    "convert_digits_to_ethiopic",
    "check_system_setup",
    "test_numeral_recognition",
]
