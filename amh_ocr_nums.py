"""
Amharic OCR with Focused Numeral Recognition
=============================================
This script specifically addresses Ethiopic numeral recognition issues in Tesseract.

The problem: Tesseract's 'amh' language pack is trained primarily on Amharic FIDEL
script, not Ethiopic numerals (፩, ፪, ፫, etc.).

Solutions implemented:
1. Character whitelist with all Ethiopic numerals
2. Multiple PSM (Page Segmentation Mode) attempts
3. Higher DPI for better numeral recognition
4. Gentler preprocessing for numeral preservation
5. Post-processing corrections for common misrecognitions
"""

import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
import tempfile
import re

# ============================================================================
# ETHIOPIC NUMERALS REFERENCE
# ============================================================================

# Complete set of Ethiopic numerals
ETHIOPIC_NUMERALS = {
    # Basic digits 1-9
    '1': '፩',   # U+1369
    '2': '፪',   # U+136A
    '3': '፫',   # U+136B
    '4': '፬',   # U+136C
    '5': '፭',   # U+136D
    '6': '፮',   # U+136E
    '7': '፯',   # U+136F
    '8': '፰',   # U+1370
    '9': '፱',   # U+1371
    # Tens
    '10': '፲',  # U+1372
    '20': '፳',  # U+1373
    '30': '፴',  # U+1374
    '40': '፵',  # U+1375
    '50': '፶',  # U+1376
    '60': '፷',  # U+1377
    '70': '፸',  # U+1378
    '80': '፹',  # U+1379
    '90': '፺',  # U+137A
    # Hundreds and thousands
    '100': '፻',  # U+137B
    '10000': '፼',  # U+137C
}

# All Ethiopic numeral characters as a string
ALL_ETHIOPIC_NUMERALS = ''.join(ETHIOPIC_NUMERALS.values())  # ፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼

# Common Amharic characters for whitelist
AMHARIC_FIDEL = "ሀሁሂሃሄህሆለሉሊላሌልሎሏሐሑሒሓሔሕሖሗመሙሚማሜምሞሟሠሡሢሣሤሥሦሧረሩሪራሬርሮሯሰሱሲሳሴስሶሷሸሹሺሻሼሽሾሿቀቁቂቃቄቅቆቈቊቋቌቍቐቑቒቓቔቕቖቘቚቛቜቝበቡቢባቤብቦቧቨቩቪቫቬቭቮቯተቱቲታቴትቶቷቸቹቺቻቼችቾቿኀኁኂኃኄኅኆኈኊኋኌኍነኑኒናኔንኖኗኘኙኚኛኜኝኞኟአኡኢኣኤእኦኧከኩኪካኬክኮኰኲኳኴኵኸኹኺኻኼኽኾዀዂዃዄዅወዉዊዋዌውዎዐዑዒዓዔዕዖዘዙዚዛዜዝዞዟዠዡዢዣዤዥዦዧየዩዪያዬይዮደዱዲዳዴድዶዷዸዹዺዻዼዽዾጀጁጂጃጄጅጆጇገጉጊጋጌግጎጐጒጓጔጕጠጡጢጣጤጥጦጧጨጩጪጫጬጭጮጯጰጱጲጳጴጵጶጷጸጹጺጻጼጽጾፀፁፂፃፄፅፆፈፉፊፋፌፍፎፏፐፑፒፓፔፕፖፗፘፙፚ"

# ============================================================================
# IMAGE PREPROCESSING
# ============================================================================

def preprocess_for_numerals(image):
    """
    Specialized preprocessing for Ethiopic numeral recognition.
    Numerals need gentler processing than text.
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Resize small images (numerals need sufficient resolution)
    height, width = gray.shape
    min_dim = min(height, width)
    if min_dim < 50:
        scale = 100 / min_dim
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Mild denoising
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Adaptive thresholding preserves numeral details better than Otsu
    binary = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        15, 10
    )
    
    # Optional: Dilate slightly to connect broken numeral strokes
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return binary

def preprocess_for_text(image):
    """Standard preprocessing for Amharic text."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Denoising
    denoised = cv2.medianBlur(gray, 5)
    
    # Otsu thresholding for text
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

# ============================================================================
# OCR FUNCTIONS
# ============================================================================

def ocr_with_whitelist(image, whitelist, lang="amh", psm=6):
    """
    Run OCR with a specific character whitelist.
    
    Args:
        image: OpenCV image (numpy array)
        whitelist: String of allowed characters
        lang: Language code
        psm: Page Segmentation Mode
            3 = Fully automatic page segmentation
            4 = Assume single column of variable sizes
            6 = Assume uniform block of text (default)
            7 = Treat as single text line
            8 = Treat as single word
            10 = Treat as single character
            11 = Sparse text
    """
    pil_img = Image.fromarray(image)
    
    # Build configuration
    config = f'--psm {psm} --oem 3'
    
    # Add whitelist if provided
    if whitelist:
        # Escape special regex characters in whitelist
        escaped_whitelist = whitelist.replace('\\', '\\\\').replace('-', '\\-')
        config += f' -c tessedit_char_whitelist={escaped_whitelist}'
    
    try:
        text = pytesseract.image_to_string(pil_img, lang=lang, config=config)
        return text.strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""

def ocr_numerals_only(image):
    """OCR focused only on Ethiopic numerals."""
    whitelist = ALL_ETHIOPIC_NUMERALS
    processed = preprocess_for_numerals(image)
    
    # Try multiple PSM modes for numerals
    results = []
    
    # PSM 10: Single character mode (good for isolated numerals)
    text = ocr_with_whitelist(processed, whitelist, lang="amh", psm=10)
    results.append(("psm10", text))
    
    # PSM 7: Single text line
    text = ocr_with_whitelist(processed, whitelist, lang="amh", psm=7)
    results.append(("psm7", text))
    
    # PSM 8: Single word
    text = ocr_with_whitelist(processed, whitelist, lang="amh", psm=8)
    results.append(("psm8", text))
    
    # Return the best result (longest non-empty)
    valid_results = [(mode, text) for mode, text in results if text]
    if valid_results:
        return max(valid_results, key=lambda x: len(x[1]))[1]
    return ""

def ocr_mixed_content(image):
    """
    OCR for mixed Amharic text and numerals.
    Uses combined whitelist of FIDEL + numerals.
    """
    whitelist = AMHARIC_FIDEL + ALL_ETHIOPIC_NUMERALS + "0123456789 .,;:!?()[]{}-'\"\\n"
    processed = preprocess_for_text(image)
    
    # Try with amh+eng for broader coverage
    text = ocr_with_whitelist(processed, whitelist, lang="amh+eng", psm=6)
    return text

def ocr_with_fallback(image):
    """
    Try multiple OCR approaches and combine results.
    """
    results = []
    
    # Approach 1: Mixed content with whitelist
    try:
        text1 = ocr_mixed_content(image)
        if text1:
            results.append(text1)
    except Exception as e:
        print(f"Approach 1 failed: {e}")
    
    # Approach 2: Numeral-focused
    try:
        text2 = ocr_numerals_only(image)
        if text2:
            results.append(text2)
    except Exception as e:
        print(f"Approach 2 failed: {e}")
    
    # Approach 3: No whitelist, just amh+eng
    try:
        processed = preprocess_for_text(image)
        pil_img = Image.fromarray(processed)
        text3 = pytesseract.image_to_string(pil_img, lang="amh+eng", config='--psm 6')
        if text3:
            results.append(text3)
    except Exception as e:
        print(f"Approach 3 failed: {e}")
    
    # Combine unique results
    if results:
        # Use the longest result as base
        best = max(results, key=len)
        return best
    
    return ""

# ============================================================================
# POST-PROCESSING
# ============================================================================

def correct_common_errors(text):
    """
    Fix common OCR errors for Ethiopic numerals.
    """
    corrections = {
        # Latin to Ethiopic
        '1': '፩',
        '2': '፪', 
        '3': '፫',
        '4': '፬',
        '5': '፭',
        '6': '፮',
        '7': '፯',
        '8': '፰',
        '9': '፱',
        '0': '፲',  # 10, not exactly 0
        
        # Common misrecognitions
        'l': '፩',   # lowercase L -> 1
        'I': '፩',   # uppercase I -> 1
        'O': '፬',   # letter O -> 4
        'S': '፭',   # letter S -> 5
        'b': '፮',   # letter b -> 6
        'T': '፯',   # letter T -> 7
        'B': '፰',   # letter B -> 8
        'g': '፱',   # letter g -> 9
        
        # Visual confusions
        '፨': '፰',   # Often confused
        '፧': '፯',   # Often confused
        '፣': '፫',   # Comma-like -> 3
    }
    
    # Apply corrections
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    return text

def extract_numerals(text):
    """Extract only Ethiopic numerals from text."""
    pattern = f'[{ALL_ETHIOPIC_NUMERALS}]+'
    return re.findall(pattern, text)

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_pdf(pdf_path, output_dir="output_texts"):
    """Process PDF with focus on numeral recognition."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Check available languages
    try:
        langs = pytesseract.get_languages()
        print(f"Available languages: {langs}")
        if 'amh' not in langs:
            print("⚠️  Warning: 'amh' language pack not found!")
            print("   Install with: sudo apt-get install tesseract-ocr-amh")
    except Exception as e:
        print(f"Could not check languages: {e}")
    
    # Get page count
    try:
        import fitz
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return
    
    print(f"\nProcessing {num_pages} pages...")
    print(f"Ethiopic numerals in whitelist: {ALL_ETHIOPIC_NUMERALS}")
    print("-" * 50)
    
    all_results = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(1, num_pages + 1):
            print(f"\nProcessing page {page_num}/{num_pages}...")
            
            try:
                # Convert page at high DPI
                images = convert_from_path(
                    pdf_path,
                    first_page=page_num,
                    last_page=page_num,
                    dpi=400
                )
                
                # Save temporary image
                temp_path = os.path.join(temp_dir, f"page_{page_num}.png")
                images[0].save(temp_path, "PNG")
                
                # Read with OpenCV
                cv_img = cv2.imread(temp_path, cv2.IMREAD_COLOR)
                
                # Run OCR with fallback
                raw_text = ocr_with_fallback(cv_img)
                
                # Post-process
                corrected_text = correct_common_errors(raw_text)
                
                # Extract numerals found
                numerals_found = extract_numerals(corrected_text)
                
                all_results.append({
                    'page': page_num,
                    'text': corrected_text,
                    'numerals': numerals_found
                })
                
                print(f"  Text length: {len(corrected_text)} chars")
                print(f"  Numerals found: {numerals_found}")
                
                # Cleanup
                os.remove(temp_path)
                
            except Exception as e:
                print(f"  Error: {e}")
                all_results.append({
                    'page': page_num,
                    'text': f"[ERROR: {e}]",
                    'numerals': []
                })
    
    # Save results
    output_file = os.path.join(output_dir, "amharic_ocr_output.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        for result in all_results:
            f.write(f"=== Page {result['page']} ===\n")
            f.write(result['text'] + "\n")
            if result['numerals']:
                f.write(f"[Numerals: {', '.join(result['numerals'])}]\n")
            f.write("\n")
    
    print("\n" + "=" * 50)
    print(f"✅ OCR complete: {output_file}")
    
    # Summary
    total_numerals = sum(len(r['numerals']) for r in all_results)
    print(f"📊 Total numerals detected: {total_numerals}")

# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_numeral_recognition():
    """Test numeral recognition with a simple image."""
    # Create a test image with Ethiopic numerals
    from PIL import ImageDraw, ImageFont
    
    img = Image.new('L', (400, 100), color=255)
    draw = ImageDraw.Draw(img)
    
    # Try to draw numerals (may need a font with Ethiopic support)
    test_text = "፩ ፪ ፫ ፬ ፭ ፮ ፯ ፰ ፱ ፲"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansEthiopic-Regular.ttf", 32)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            font = ImageFont.load_default()
    
    draw.text((10, 30), test_text, fill=0, font=font)
    
    # Convert to OpenCV format
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_GRAY2BGR)
    
    # Test OCR
    print("Testing numeral recognition...")
    print(f"Expected: {test_text}")
    
    result = ocr_numerals_only(cv_img)
    print(f"Got:      {result}")
    
    return result

if __name__ == "__main__":
    import sys
    
    pdf_path = "/home/dev1/p.i.s.f/books/books/fiker_split/page_004.pdf"
    
    # Allow command-line override
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    process_pdf(pdf_path)
