"""
Post-processing and error corrections for Amharic text and Ethiopic numerals.
"""

import re

from ..constants import (
    ALL_ETHIOPIC_NUMERALS,
    ETHIOPIC_NUMERALS,
    LATIN_TO_ETHIOPIC_LOOKALIKES,
    VISUAL_CONFUSIONS,
)


def correct_visual_confusions(text: str) -> str:
    """
    Safe corrections that fix obvious OCR confusion symbols globally.
    Only applies to characters that are never valid Amharic text:
    - '፨' (paragraph separator) -> '፰' (8)
    Note: '፣' (Ethiopic comma) and '፧' (Ethiopic question mark) are valid
    Amharic punctuation and are NOT replaced here.
    """
    for wrong, correct in VISUAL_CONFUSIONS.items():
        text = text.replace(wrong, correct)
    return text

def correct_latin_lookalikes(text: str) -> str:
    """
    Fix common OCR errors for Ethiopic numerals.

    IMPORTANT: corrections are applied token-by-token and ONLY to tokens that
    are already numeral-zone candidates (i.e. tokens containing at least one
    real Ethiopic numeral character or that consist solely of Latin look-alikes).
    This prevents corrupting legitimate Amharic words or English abbreviations
    that contain the same Latin glyphs.
    """
    latin_lookalikes = ''.join(re.escape(c) for c in LATIN_TO_ETHIOPIC_LOOKALIKES)
    numeral_zone_pattern = re.compile(
        rf'[{re.escape(ALL_ETHIOPIC_NUMERALS)}{latin_lookalikes}]*'
        rf'[{re.escape(ALL_ETHIOPIC_NUMERALS)}]'
        rf'[{re.escape(ALL_ETHIOPIC_NUMERALS)}{latin_lookalikes}]*'
    )

    def fix_token(m: re.Match) -> str:
        token = m.group(0)
        for wrong, correct in LATIN_TO_ETHIOPIC_LOOKALIKES.items():
            token = token.replace(wrong, correct)
        return token

    return numeral_zone_pattern.sub(fix_token, text)

def correct_common_errors(text: str) -> str:
    """
    Full error correction pipeline as defined in amh_ocr_nums.py:
    1. Apply Ethiopic-only visual corrections globally.
    2. Apply Latin-to-Ethiopic look-alike replacements within numeral zones.
    """
    text = correct_visual_confusions(text)
    text = correct_latin_lookalikes(text)
    return text

def deduplicate_numeral_loops(text: str) -> str:
    """
    Remove runs of the same Ethiopic numeral that look like OCR looping artifacts.
    E.g. ፻፻፻ (three hundreds in a row with no valid composite meaning) is
    collapsed to ፻. Legitimate composites like ፻፳ (120) are left intact.
    Collapses 3+ consecutive identical numeral characters to 2 max.
    """
    dedup_pattern = re.compile(
        rf'([{re.escape(ALL_ETHIOPIC_NUMERALS)}])\1{{2,}}'
    )
    return dedup_pattern.sub(r'\1\1', text)

# Alias for backwards compatibility
_deduplicate_numeral = deduplicate_numeral_loops

def convert_digits_to_ethiopic(text: str) -> str:
    """Converts standard Latin digits (1, 2, 3...) to Ethiopic ones (፩, ፪, ፫...)."""
    # Sort keys by length descending to replace "10000", "100", "10" before "1"
    sorted_keys = sorted(ETHIOPIC_NUMERALS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        text = text.replace(key, ETHIOPIC_NUMERALS[key])
    return text

def extract_ethiopic_numerals(text: str) -> list[str]:
    """Extract all runs of Ethiopic numerals from text."""
    pattern = rf'[{ALL_ETHIOPIC_NUMERALS}]+'
    return re.findall(pattern, text)

# Alias
extract_numerals = extract_ethiopic_numerals

def post_process_text(text: str, is_numeral_heavy: bool = False) -> str:
    """
    Applies the full post-processing pipeline to OCR text:
    1. Correct globally-safe visual confusions (e.g. ፨ → ፰).
    2. If numeral-heavy, apply Latin-lookalike corrections and digit conversion.
       These are restricted to numeral-heavy pages to avoid corrupting body text
       that happens to contain Latin characters adjacent to Ethiopic numerals.
    3. Remove OCR duplication loops.
    """
    # Step 1: always safe — only replaces characters that are never valid body text
    text = correct_visual_confusions(text)

    # Step 2: numeral-zone corrections — only on pages dominated by numerals
    if is_numeral_heavy:
        text = correct_latin_lookalikes(text)
        text = convert_digits_to_ethiopic(text)

    # Step 3: collapse repeated numeral artifacts (safe on all pages)
    text = deduplicate_numeral_loops(text)
    return text
