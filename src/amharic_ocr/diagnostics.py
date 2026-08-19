"""
Diagnostics and system verification for Amharic OCR & Ethiopic Numeral Recognition.
"""

import os
import sys

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont

from .engines.tesseract import TesseractEngine


def test_numeral_recognition() -> str:
    """
    Test Ethiopic numeral recognition with an in-memory test image.
    Matches test_numeral_recognition in amh_ocr_nums.py.
    """
    img = Image.new('L', (400, 100), color=255)
    draw = ImageDraw.Draw(img)
    
    test_text = "፩ ፪ ፫ ፬ ፭ ፮ ፯ ፰ ፱ ፲"
    
    font = None
    font_candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansEthiopic-Regular.ttf",
        "/usr/share/fonts/truetype/abyssinica/AbyssinicaSIL-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 32)
                break
            except OSError:
                pass
                
    if font is None:
        font = ImageFont.load_default()
        
    draw.text((10, 30), test_text, fill=0, font=font)
    
    # Convert to OpenCV format
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_GRAY2BGR)
    
    print("Testing Ethiopic numeral recognition...")
    print(f"Expected: {test_text}")
    
    engine = TesseractEngine()
    result = engine.ocr_numerals_only(cv_img)
    print(f"Got:      {result.text}")
    
    return result.text

def check_system_setup():
    """Run full environment diagnostics."""
    print("=" * 60)
    print("AMHARIC OCR ENVIRONMENT DIAGNOSTICS")
    print("=" * 60)
    
    # 1. Check Python
    print(f"Python Version: {sys.version.splitlines()[0]}")
    
    # 2. Check OpenCV
    print(f"OpenCV Version: {cv2.__version__}")
    
    # 3. Check PyMuPDF (fitz)
    try:
        import fitz
        print(f"PyMuPDF (fitz) Version: {getattr(fitz, '__version__', 'Installed')}")
    except ImportError:
        print("❌ PyMuPDF (fitz) is NOT installed!")
        
    # 4. Check EasyOCR
    try:
        import importlib.util
        if importlib.util.find_spec("easyocr") is not None:
            print("✅ EasyOCR is installed")
        else:
            print("⚠️  EasyOCR is NOT installed (optional fallback engine)")
    except Exception:  # noqa: BLE001
        print("⚠️  EasyOCR is NOT installed (optional fallback engine)")

    # 5. Check Tesseract Setup
    print("\n--- TESSERACT SETUP ---")
    try:
        langs = pytesseract.get_languages()
        print(f"Available languages ({len(langs)} total): {langs}")
        
        if 'amh' in langs:
            print("  ✅ 'amh' (Amharic) language pack is INSTALLED")
        else:
            print("  ❌ 'amh' (Amharic) language pack is NOT installed!")
            print("     To install it, run: sudo apt-get install tesseract-ocr-amh")
            
        if 'eng' in langs:
            print("  ✅ 'eng' (English) language pack is INSTALLED")
        else:
            print("  ⚠️  'eng' (English) language pack is NOT installed")
            
    except (pytesseract.TesseractNotFoundError, Exception) as e:  # noqa: BLE001
        print(f"❌ Error querying Tesseract languages: {e}")
        print("   To install, run: sudo apt-get install tesseract-ocr")
        
    tessdata = os.environ.get('TESSDATA_PREFIX', 'Not set')
    print(f"TESSDATA_PREFIX env: {tessdata}")
    
    # 6. Test Numeral Recognition
    print("\n--- ETHIOPIC NUMERAL TEST ---")
    test_numeral_recognition()
    
    print("=" * 60)

if __name__ == "__main__":
    check_system_setup()
