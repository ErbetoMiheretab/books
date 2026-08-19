"""
Post-processing and error corrections.
"""

from .corrections import (
    convert_digits_to_ethiopic,
    correct_common_errors,
    correct_latin_lookalikes,
    correct_visual_confusions,
    deduplicate_numeral_loops,
    extract_ethiopic_numerals,
    post_process_text,
)

__all__ = [
    "convert_digits_to_ethiopic",
    "correct_common_errors",
    "correct_latin_lookalikes",
    "correct_visual_confusions",
    "deduplicate_numeral_loops",
    "extract_ethiopic_numerals",
    "post_process_text",
]
