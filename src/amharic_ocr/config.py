"""
Configuration options for the Amharic OCR pipeline.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class OCRConfig:
    # PDF rendering DPI (default 400 for maximum numeral clarity as in amh_ocr_nums.py)
    dpi: int = 400
    
    # Split double-page scans horizontally
    split_pages: bool = False
    
    # Engines to enable
    use_tesseract: bool = True
    use_easyocr: bool = False
    
    # Languages to load
    languages: List[str] = field(default_factory=lambda: ["amh", "eng"])
    
    # Tesseract configuration
    tesseract_psm: int = 6
    tesseract_oem: int = 3
    
    # EasyOCR configuration
    easyocr_gpu: bool = False
    
    # Error detection: flag page if character count is below this
    min_char_threshold: int = 50
    
    # Paths
    output_dir: str = "output_texts"
    
    # Numeral config
    detect_numerals: bool = True
