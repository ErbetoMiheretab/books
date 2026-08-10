"""
Diagnostic script for Amharic/Ethiopic OCR issues
=================================================
This script helps diagnose why Amharic numerals are not being recognized.
"""

import os
import sys
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

# Ethiopic numeral Unicode range: U+1369 to U+137C
ETHIOPIC_NUMERALS = "፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼"

def check_tesseract_setup():
    """Check Tesseract installation and available languages."""
    print("=" * 60)
    print("TESSERACT SETUP DIAGNOSTICS")
    print("=" * 60)
    
    # Check Tesseract path
    try:
        tess_path = pytesseract.pytesseract.tesseract_cmd
        print(f"Tesseract command: {tess_path}")
    except Exception as e:
        print(f"❌ Error getting Tesseract path: {e}")
    
    # Check available languages
    try:
        langs = pytesseract.get_languages()
        print(f"\nAvailable languages ({len(langs)} total):")
        
        relevant = [l for l in langs if l in ['amh', 'eng', 'osd', 'Ethiopic'] or 'ethio' in l.lower()]
        if relevant:
            print(f"  Relevant for Amharic: {relevant}")
        else:
            print("  ⚠️  'amh' language pack NOT found!")
            print("     Install with: sudo apt-get install tesseract-ocr-amh")
        
        if 'amh' in langs:
            print("  ✅ 'amh' language pack is installed")
        
    except Exception as e:
        print(f"❌ Error checking languages: {e}")
    
    # Check TESSDATA_PREFIX
    tessdata = os.environ.get('TESSDATA_PREFIX', 'Not set')
    print(f"\nTESSDATA_PREFIX: {tessdata}")
    
    print()

def test_basic_ocr():
    """Test basic OCR functionality."""
    print("=" * 60)
    print("BASIC OCR TEST")
    print("=" * 60)
    
    # Create a simple test image with English text
    img = Image.new('L', (200, 50), color=255)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 10), "Hello 123", fill=0, font=font)
    
    try:
        text = pytesseract.image_to_string(img, lang='eng')
        print(f"Test text: 'Hello 123'")
        print(f"OCR result: '{text.strip()}'")
        if 'Hello' in text or '123' in text:
            print("✅ Basic OCR is working")
        else:
            print("⚠️  Basic OCR may have issues")
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
    
    print()

def test_amharic_script():
    """Test Amharic script recognition."""
    print("=" * 60)
    print("AMHARIC SCRIPT TEST")
    print("=" * 60)
    
    # Create test image with Amharic text
    img = Image.new('L', (300, 80), color=255)
    draw = ImageDraw.Draw(img)
    
    # Try to find a font with Ethiopic support
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansEthiopic-Regular.ttf",
        "/usr/share/fonts/truetype/abyssinica/AbyssinicaSIL-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 32)
                print(f"Using font: {fp}")
                break
            except:
                pass
    
    if font is None:
        font = ImageFont.load_default()
        print("Using default font (may not support Ethiopic)")
    
    # Amharic text: "አማርኛ" (Amharic)
    test_text = "አማርኛ"
    draw.text((10, 20), test_text, fill=0, font=font)
    
    # Save for inspection
    img.save("/mnt/okcomputer/output/test_amharic.png")
    print(f"Test image saved to: /mnt/okcomputer/output/test_amharic.png")
    
    # Test with amh language
    try:
        text = pytesseract.image_to_string(img, lang='amh')
        print(f"Test text: '{test_text}'")
        print(f"OCR result: '{text.strip()}'")
        
        # Check if any Amharic characters were recognized
        if any('\u1200' <= c <= '\u137F' for c in text):
            print("✅ Amharic script recognition is working")
        else:
            print("⚠️  No Amharic characters detected in output")
            
    except Exception as e:
        print(f"❌ Amharic OCR test failed: {e}")
    
    print()

def test_ethiopic_numerals():
    """Test Ethiopic numeral recognition specifically."""
    print("=" * 60)
    print("ETHIOPIC NUMERAL TEST")
    print("=" * 60)
    
    # Create test image with Ethiopic numerals
    img = Image.new('L', (500, 100), color=255)
    draw = ImageDraw.Draw(img)
    
    # Try to find a font
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansEthiopic-Regular.ttf",
        "/usr/share/fonts/truetype/abyssinica/AbyssinicaSIL-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 36)
                print(f"Using font: {fp}")
                break
            except:
                pass
    
    if font is None:
        font = ImageFont.load_default()
        print("Using default font")
    
    # Ethiopic numerals 1-10
    test_numerals = "፩ ፪ ፫ ፬ ፭ ፮ ፯ ፰ ፱ ፲"
    draw.text((10, 30), test_numerals, fill=0, font=font)
    
    # Save for inspection
    img.save("/mnt/okcomputer/output/test_numerals.png")
    print(f"Test image saved to: /mnt/okcomputer/output/test_numerals.png")
    
    # Test with different configurations
    print(f"\nTest numerals: {test_numerals}")
    print(f"Unicode check: {[f'U+{ord(c):04X}' for c in test_numerals if c.strip()]}")
    
    configs = [
        ("amh, default", "amh", ""),
        ("amh+eng", "amh+eng", ""),
        ("amh, whitelist", "amh", f"-c tessedit_char_whitelist={ETHIOPIC_NUMERALS}"),
        ("amh, PSM 10", "amh", "--psm 10"),
        ("amh, PSM 7", "amh", "--psm 7"),
    ]
    
    for name, lang, config in configs:
        try:
            text = pytesseract.image_to_string(img, lang=lang, config=config)
            numerals_found = [c for c in text if c in ETHIOPIC_NUMERALS]
            print(f"\n  {name}:")
            print(f"    Output: '{text.strip()}'")
            print(f"    Numerals found: {len(numerals_found)} - {numerals_found}")
        except Exception as e:
            print(f"\n  {name}: ❌ Error - {e}")
    
    print()

def test_with_whitelist():
    """Test the effect of character whitelisting."""
    print("=" * 60)
    print("WHITELIST EFFECTIVENESS TEST")
    print("=" * 60)
    
    # Create test image
    img = Image.new('L', (400, 80), color=255)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font = ImageFont.load_default()
    
    # Mixed content
    test_text = "Text 123 ፩፪፫"
    draw.text((10, 20), test_text, fill=0, font=font)
    
    print(f"Test text: {test_text}")
    
    # Test without whitelist
    try:
        text_no_wl = pytesseract.image_to_string(img, lang='amh')
        print(f"Without whitelist: '{text_no_wl.strip()}'")
    except Exception as e:
        print(f"Without whitelist: Error - {e}")
    
    # Test with whitelist
    whitelist = ETHIOPIC_NUMERALS + "ABCabc "
    try:
        text_with_wl = pytesseract.image_to_string(img, lang='amh', 
            config=f'-c tessedit_char_whitelist={whitelist}')
        print(f"With whitelist: '{text_with_wl.strip()}'")
    except Exception as e:
        print(f"With whitelist: Error - {e}")
    
    print()

def suggest_fixes():
    """Suggest potential fixes based on diagnostics."""
    print("=" * 60)
    print("SUGGESTED FIXES")
    print("=" * 60)
    
    print("""
If Ethiopic numerals are not being recognized, try these fixes:

1. INSTALL/UPDATE LANGUAGE PACK:
   sudo apt-get update
   sudo apt-get install tesseract-ocr-amh
   
   Or download manually from:
   https://github.com/tesseract-ocr/tessdata

2. USE CHARACTER WHITELIST:
   Add all Ethiopic numerals to the whitelist:
   
   ETHIOPIC_NUMERALS = "፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼"
   config = f'--psm 6 -c tessedit_char_whitelist={ETHIOPIC_NUMERALS}'
   text = pytesseract.image_to_string(img, lang='amh', config=config)

3. TRY DIFFERENT PAGE SEGMENTATION MODES:
   --psm 6  (Default, uniform text block)
   --psm 7  (Single text line)
   --psm 8  (Single word)
   --psm 10 (Single character - good for isolated numerals)
   --psm 11 (Sparse text)

4. USE HIGHER DPI:
   Ethiopic numerals need good resolution. Use 300-400 DPI.

5. TRY 'amh+eng' LANGUAGE COMBINATION:
   text = pytesseract.image_to_string(img, lang='amh+eng')

6. GENTLER PREPROCESSING:
   Numerals are often destroyed by aggressive thresholding.
   Use adaptive thresholding instead of Otsu.

7. POST-PROCESSING CORRECTIONS:
   Map common misrecognitions:
   'l' -> '፩', 'O' -> '፬', etc.

8. CONSIDER ALTERNATIVE OCR ENGINES:
   - EasyOCR (has Ethiopic support)
   - Google Vision API
   - Custom-trained Tesseract model
""")

if __name__ == "__main__":
    check_tesseract_setup()
    test_basic_ocr()
    test_amharic_script()
    test_ethiopic_numerals()
    test_with_whitelist()
    suggest_fixes()
