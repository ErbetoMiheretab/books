import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import multiprocessing as mp
import tempfile
import numpy as np

def preprocess_image(image_array):
    """
    Refined preprocessing.
    Removed medianBlur to prevent 'smearing' thin Amharic number strokes.
    """
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_array

    # Otsu's thresholding works best for high-contrast book scans
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img

def run_tesseract(image_array):
    """
    Run Tesseract with a focus on the Ethiopic syllabary and numerals.
    """
    processed = preprocess_image(image_array)
    pil_img = Image.fromarray(processed)
    
    # Using 'amh' for language. 
    # --psm 6 (Assume a single uniform block of text) is the key for book pages.
    # --oem 1 uses the LSTM engine which is better for Amharic script.
    custom_config = r'--psm 6 --oem 1'
    
    text = pytesseract.image_to_string(pil_img, lang="amh", config=custom_config)
    return text

def process_page(args):
    """Process single PDF page at a higher resolution for number clarity."""
    page_num, pdf_path, temp_dir = args
    
    # CRITICAL CHANGE: 
    # Increased DPI to 500. Ethiopic numbers have tiny cross-sections.
    # 300 DPI often merges the lines of ፯ or ፰.
    images = convert_from_path(
        pdf_path, 
        first_page=page_num, 
        last_page=page_num,
        dpi=500 
    )
    
    if not images:
        return {'page': page_num, 'text': ""}

    # Convert to numpy array for processing
    cv_img = np.array(images[0])
    
    # OCR
    text = run_tesseract(cv_img)
    
    return {'page': page_num, 'text': text}

def main(pdf_path, output_dir="output_texts"):
    os.makedirs(output_dir, exist_ok=True)
    
    import fitz
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    
    print(f"🚀 Processing {num_pages} pages using High-Resolution Amharic OCR...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        tasks = [(i+1, pdf_path, temp_dir) for i in range(num_pages)]
        
        # Using a pool to maintain the speed of your first script
        with mp.Pool(processes=min(mp.cpu_count(), 4)) as pool:
            results = pool.map(process_page, tasks)
        
        # Save results
        output_file = os.path.join(output_dir, "amharic_ocr_final.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for result in sorted(results, key=lambda x: x['page']):
                f.write(f"=== Page {result['page']} ===\n")
                f.write(result['text'] + "\n\n")
        
        print(f"✅ OCR complete: {output_file}")

if __name__ == "__main__":
    main("/home/dev1/p.i.s.f/books/books/fiker_split/page_004.pdf")