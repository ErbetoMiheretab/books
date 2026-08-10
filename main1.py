import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import multiprocessing as mp
import tempfile
from functools import partial

def preprocess_image(image_array):
    """Optimized preprocessing for Amharic script."""
    img = cv2.medianBlur(image_array, 3)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img

def run_tesseract(image_array):
    """Run Tesseract with Amharic language pack."""
    processed = preprocess_image(image_array)
    pil_img = Image.fromarray(processed)
    # Tesseract uses 'amh' for Amharic
    text = pytesseract.image_to_string(pil_img, lang="amh")
    return text

def process_page(args):
    """Process single PDF page."""
    page_num, pdf_path, temp_dir = args
    
    # Convert single page
    images = convert_from_path(
        pdf_path, 
        first_page=page_num, 
        last_page=page_num,
        dpi=300
    )
    
    # Save temp image
    temp_path = os.path.join(temp_dir, f"page_{page_num}_{os.getpid()}.png")
    images[0].save(temp_path, "PNG")
    
    # Read with OpenCV for processing
    cv_img = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
    
    # OCR
    text = run_tesseract(cv_img)
    
    # Cleanup
    os.remove(temp_path)
    
    return {'page': page_num, 'text': text}

def main(pdf_path, output_dir="output_texts"):
    os.makedirs(output_dir, exist_ok=True)
    
    # Get page count
    import fitz
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    
    print(f"Processing {num_pages} pages with Tesseract (Amharic)...")
    
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
                f.write(result['text'] + "\n\n")
        
        print(f"✅ OCR complete: {output_file}")

if __name__ == "__main__":
    main("/home/dev1/p.i.s.f/books/books/fiker_split/page_004.pdf")