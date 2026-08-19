"""
Post-processing and error corrections.
"""

from .corrections import (
    correct_common_errors,
    correct_visual_confusions,
    correct_latin_lookalikes,
    deduplicate_numeral_loops,
    convert_digits_to_ethiopic,
    extract_ethiopic_numerals,
    post_process_text,
)

__all__ = [
    "correct_common_errors",
    "correct_visual_confusions",
    "correct_latin_lookalikes",
    "deduplicate_numeral_loops",
    "convert_digits_to_ethiopic",
    "extract_ethiopic_numerals",
    "post_process_text",
]
