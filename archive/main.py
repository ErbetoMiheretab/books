import os
import pytesseract
import easyocr
from pdf2image import convert_from_path
from PIL import Image
import cv2
import multiprocessing as mp
from functools import partial
import tempfile

# Global per-process storage
_easyocr_reader = None

def init_worker(gpu=False):
    """Initialize EasyOCR once per worker."""
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(['amh'], gpu=gpu, verbose=False)

def preprocess_image(image_array):
    """Optimized preprocessing."""
    img = cv2.medianBlur(image_array, 3)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img

def run_tesseract(image_array):
    """Run Tesseract on preprocessed array."""
    processed = preprocess_image(image_array)
    pil_img = Image.fromarray(processed)
    return pytesseract.image_to_string(pil_img, lang="amh")

def run_easyocr(image_path):
    """Use cached EasyOCR reader."""
    global _easyocr_reader
    result = _easyocr_reader.readtext(image_path, detail=0, paragraph=True)
    return " ".join(result)

def process_page(args):
    """Process single page with isolated temp file."""
    page_num, pdf_path, temp_dir = args
    
    # Convert single page (memory efficient)
    images = convert_from_path(
        pdf_path, 
        first_page=page_num, 
        last_page=page_num,
        dpi=300  # Good balance of quality/speed
    )
    
    # Save to unique temp file
    temp_path = os.path.join(temp_dir, f"page_{page_num}_{os.getpid()}.png")
    images[0].save(temp_path, "PNG")
    
    # Convert to OpenCV format for Tesseract
    cv_img = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
    
    # Run OCRs
    tesseract_text = run_tesseract(cv_img)
    easyocr_text = run_easyocr(temp_path)
    
    # Cleanup
    os.remove(temp_path)
    
    return {
        'page': page_num,
        'tesseract': tesseract_text,
        'easyocr': easyocr_text
    }

def main(pdf_path, output_dir="output_texts", use_gpu=False):
    os.makedirs(output_dir, exist_ok=True)
    
    # Fast page count without full conversion
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Prepare arguments
        tasks = [(i+1, pdf_path, temp_dir) for i in range(num_pages)]
        
        # Process with pool
        with mp.Pool(
            processes=min(mp.cpu_count(), 4),  # Limit to prevent memory issues
            initializer=partial(init_worker, gpu=use_gpu)
        ) as pool:
            results = pool.map(process_page, tasks)
        
        # Save results
        output_file = os.path.join(output_dir, "ocr_output.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for result in sorted(results, key=lambda x: x['page']):
                f.write(f"=== Page {result['page']} ===\n")
                f.write(f"Tesseract:\n{result['tesseract']}\n\n")
                f.write(f"EasyOCR:\n{result['easyocr']}\n")
                f.write("="*80 + "\n")
        
        print(f"OCR complete. Output saved to: {output_file}")

if __name__ == "__main__":
    main("/home/dev1/p.i.s.f/books/books/fiker_split/page_004.pdf")