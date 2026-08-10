import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import multiprocessing as mp
import tempfile
from functools import partial

# Ethiopic numerals whitelist
ETHIOPIC_NUMERALS = "፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼"
# Amharic characters range (basic FIDEL)
AMHARIC_CHARS = "ሀሁሂሃሄህሆለሉሊላሌልሎሏሐሑሒሓሔሕሖሗመሙሚማሜምሞሟሠሡሢሣሤሥሦሧረሩሪራሬርሮሯሰሱሲሳሴስሶሷሸሹሺሻሼሽሾሿቀቁቂቃቄቅቆቈቊቋቌቍቐቑቒቓቔቕቖቘቚቛቜቝበቡቢባቤብቦቧቨቩቪቫቬቭቮቯተቱቲታቴትቶቷቸቹቺቻቼችቾቿኀኁኂኃኄኅኆኈኊኋኌኍነኑኒናኔንኖኗኘኙኚኛኜኝኞኟአኡኢኣኤእኦኧከኩኪካኬክኮኰኲኳኴኵኸኹኺኻኼኽኾዀዂዃዄዅወዉዊዋዌውዎዐዑዒዓዔዕዖዘዙዚዛዜዝዞዟዠዡዢዣዤዥዦዧየዩዪያዬይዮደዱዲዳዴድዶዷዸዹዺዻዼዽዾጀጁጂጃጄጅጆጇገጉጊጋጌግጎጐጒጓጔጕጠጡጢጣጤጥጦጧጨጩጪጫጬጭጮጯጰጱጲጳጴጵጶጷጸጹጺጻጼጽጾፀፁፂፃፄፅፆፈፉፊፋፌፍፎፏፐፑፒፓፔፕፖፗፘፙፚ"
# Latin digits and common punctuation
LATIN_CHARS = "0123456789.,;:!?()[]{}-'\" \\\n"

def preprocess_image(image_array, is_numeral_heavy=False):
    """
    Optimized preprocessing for Amharic script and numerals.
    
    Args:
        image_array: Input image as numpy array
        is_numeral_heavy: If True, use gentler preprocessing for numerals
    """
    # Make a copy to avoid modifying original
    img = image_array.copy()
    
    # Apply mild denoising - median blur with smaller kernel for numerals
    if is_numeral_heavy:
        img = cv2.medianBlur(img, 3)
    else:
        img = cv2.medianBlur(img, 5)
    
    # Resize if image is too small (helps with numeral recognition)
    height, width = img.shape[:2]
    if height < 100 or width < 100:
        scale = max(2, 200 // min(height, width))
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Adaptive thresholding works better for numerals than Otsu
    if is_numeral_heavy:
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    else:
        # Otsu thresholding for text
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return img

def run_tesseract(image_array, lang="amh", whitelist=None, psm=6):
    """
    Run Tesseract with Amharic language pack and custom configurations.
    
    Args:
        image_array: Preprocessed image as numpy array
        lang: Language code(s) to use
        whitelist: Optional character whitelist
        psm: Page Segmentation Mode (default 6 = uniform block of text)
    """
    processed = preprocess_image(image_array)
    pil_img = Image.fromarray(processed)
    
    # Build config string
    config = f'--psm {psm} --oem 3'
    
    if whitelist:
        config += f' -c tessedit_char_whitelist={whitelist}'
    
    # Run OCR
    text = pytesseract.image_to_string(pil_img, lang=lang, config=config)
    return text

def run_tesseract_multiple_configs(image_array):
    """
    Try multiple Tesseract configurations and return the best result.
    This is useful for handling both Amharic text and numerals.
    """
    results = []
    
    # Configuration 1: Amharic with numeral whitelist
    whitelist = ETHIOPIC_NUMERALS + AMHARIC_CHARS + LATIN_CHARS
    try:
        text1 = run_tesseract(image_array, lang="amh", whitelist=whitelist, psm=6)
        results.append(("amh+whitelist", text1))
    except Exception as e:
        print(f"Config 1 failed: {e}")
    
    # Configuration 2: Try Ethiopic script (may have better numeral support)
    try:
        text2 = run_tesseract(image_array, lang="amh+eng", psm=6)
        results.append(("amh+eng", text2))
    except Exception as e:
        print(f"Config 2 failed: {e}")
    
    # Configuration 3: Single character mode (good for isolated numerals)
    try:
        text3 = run_tesseract(image_array, lang="amh", whitelist=whitelist, psm=10)
        results.append(("amh+psm10", text3))
    except Exception as e:
        print(f"Config 3 failed: {e}")
    
    # Configuration 4: Sparse text mode
    try:
        text4 = run_tesseract(image_array, lang="amh", whitelist=whitelist, psm=11)
        results.append(("amh+psm11", text4))
    except Exception as e:
        print(f"Config 4 failed: {e}")
    
    # Return the longest result (usually the most complete)
    if results:
        best = max(results, key=lambda x: len(x[1]))
        return best[1]
    
    return ""

def detect_if_numeral_heavy(image_array):
    """
    Simple heuristic to detect if image contains mostly numerals.
    """
    # Check aspect ratio - numerals tend to be more square or narrow
    height, width = image_array.shape[:2]
    aspect_ratio = width / height if height > 0 else 1
    
    # Count connected components
    _, binary = cv2.threshold(image_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    
    # If many small components, might be numerals
    small_components = sum(1 for i in range(1, num_labels) 
                          if stats[i, cv2.CC_STAT_WIDTH] < width * 0.2)
    
    return small_components > 5

def process_page(args):
    """Process single PDF page with improved OCR."""
    page_num, pdf_path, temp_dir = args
    
    try:
        # Convert single page at higher DPI for better numeral recognition
        images = convert_from_path(
            pdf_path, 
            first_page=page_num, 
            last_page=page_num,
            dpi=400  # Increased DPI for better numeral recognition
        )
        
        # Save temp image
        temp_path = os.path.join(temp_dir, f"page_{page_num}_{os.getpid()}.png")
        images[0].save(temp_path, "PNG", dpi=(400, 400))
        
        # Read with OpenCV for processing
        cv_img = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
        
        if cv_img is None:
            raise ValueError(f"Could not read image: {temp_path}")
        
        # Detect if page is numeral-heavy
        is_numeral_heavy = detect_if_numeral_heavy(cv_img)
        
        # OCR with multiple configurations
        text = run_tesseract_multiple_configs(cv_img)
        
        # Cleanup
        os.remove(temp_path)
        
        return {'page': page_num, 'text': text, 'numeral_heavy': is_numeral_heavy}
        
    except Exception as e:
        print(f"Error processing page {page_num}: {e}")
        return {'page': page_num, 'text': f"[ERROR: {e}]", 'numeral_heavy': False}

def post_process_amharic_text(text):
    """
    Post-process OCR output to fix common Amharic numeral issues.
    """
    # Common misrecognitions of Ethiopic numerals
    corrections = {
        '፨': '፰',  # Often confused
        '፧': '፯',  # Often confused
        'l': '፩',  # Latin 'l' misrecognized as 1
        'I': '፩',  # Capital I misrecognized as 1
        'O': '፬',  # Capital O misrecognized as 4
        'S': '፭',  # Capital S misrecognized as 5
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    return text

def main(pdf_path, output_dir="output_texts", use_multiple_configs=True):
    os.makedirs(output_dir, exist_ok=True)
    
    # Get page count
    try:
        import fitz
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return
    
    print(f"Processing {num_pages} pages with Tesseract (Amharic + Numerals)...")
    print(f"Using multiple OCR configurations: {use_multiple_configs}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        tasks = [(i+1, pdf_path, temp_dir) for i in range(num_pages)]
        
        # Use fewer processes to avoid memory issues
        with mp.Pool(processes=min(mp.cpu_count(), 4)) as pool:
            results = pool.map(process_page, tasks)
        
        # Save results
        output_file = os.path.join(output_dir, "amharic_ocr_output.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for result in sorted(results, key=lambda x: x['page']):
                f.write(f"=== Page {result['page']} ===\n")
                if result.get('numeral_heavy'):
                    f.write("[Detected as numeral-heavy page]\n")
                processed_text = post_process_amharic_text(result['text'])
                f.write(processed_text + "\n\n")
        
        print(f"✅ OCR complete: {output_file}")
        
        # Print summary
        numeral_pages = sum(1 for r in results if r.get('numeral_heavy'))
        print(f"📊 Summary: {numeral_pages}/{num_pages} pages detected as numeral-heavy")

if __name__ == "__main__":
    # Check if tesseract has Amharic language pack
    try:
        langs = pytesseract.get_languages()
        print(f"Available Tesseract languages: {langs}")
        if 'amh' not in langs:
            print("⚠️ Warning: 'amh' language pack not found!")
            print("Install it with: sudo apt-get install tesseract-ocr-amh")
    except Exception as e:
        print(f"Could not check languages: {e}")
    
    main("/home/dev1/p.i.s.f/books/books/fiker_split/page_004.pdf")
