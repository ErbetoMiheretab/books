import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
import multiprocessing as mp
import tempfile

# === CONFIGURATION ===
# Set to True if your PDF has two book pages per single PDF page
SPLIT_PAGES = True 

# Ethiopic Numerals and Punctuation for better recognition
ETHIOPIC_NUMERALS = "፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼"
ETHIOPIC_PUNCTUATION = "።፣؛፥፦፧፨"

def preprocess_image(image_array):
    """Optimized preprocessing for Amharic script and numbers."""
    if len(image_array.shape) == 3:
        image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    
    # 1. Resize if too small (helps with tiny numbers)
    if image_array.shape[0] < 1500:
        image_array = cv2.resize(image_array, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # 2. Bilateral Filter: Removes noise while keeping edges sharp
    img = cv2.bilateralFilter(image_array, 9, 75, 75)
    
    # 3. Adaptive Thresholding
    img = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )
    
    return img

def run_tesseract(image_array):
    """Run Tesseract with specific config."""
    processed = preprocess_image(image_array)
    pil_img = Image.fromarray(processed)
    
    # --psm 6 is usually best for book pages (Assume a single uniform block of text)
    custom_config = r'--psm 6'
    
    # Use amh+eng to catch both Amharic and any Western digits/text
    text = pytesseract.image_to_string(pil_img, lang="amh+eng", config=custom_config)
    return text

def split_image_horizontally(cv_img):
    """Splits an image into Left and Right pages."""
    height, width = cv_img.shape[:2]
    midpoint = width // 2
    
    # Crop: [Start_Y:End_Y, Start_X:End_X]
    left_page = cv_img[0:height, 0:midpoint]
    right_page = cv_img[0:height, midpoint:width]
    
    return [left_page, right_page]

def process_page(args):
    """Process single PDF page (handling potential 2-page splits)."""
    page_num, pdf_path, temp_dir, should_split = args
    
    results = []
    
    try:
        # Convert PDF page to image
        images = convert_from_path(
            pdf_path, 
            first_page=page_num, 
            last_page=page_num,
            dpi=300 # 300 is usually sufficient; go to 400 if numbers are still blurry
        )
        
        if not images:
            return []

        # Save temp image to read with OpenCV
        temp_path = os.path.join(temp_dir, f"page_{page_num}_{os.getpid()}.png")
        images[0].save(temp_path, "PNG")
        cv_img = cv2.imread(temp_path) # Read as color initially
        
        # Split logic
        page_images = []
        if should_split:
            # Returns [Left Image, Right Image]
            split_imgs = split_image_horizontally(cv_img)
            page_images.append(('a', split_imgs[0])) # 'a' for Left
            page_images.append(('b', split_imgs[1])) # 'b' for Right
        else:
            page_images.append(('', cv_img))

        # Process each sub-page
        for suffix, img in page_images:
            text = run_tesseract(img)
            results.append({
                'page': f"{page_num}{suffix}", # e.g., 5a, 5b
                'text': text
            })
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return results
        
    except Exception as e:
        print(f"Error processing page {page_num}: {e}")
        return [{'page': page_num, 'text': f"[ERROR] {e}"}]

def main(pdf_path, output_dir="output_texts", split_pages=False):
    os.makedirs(output_dir, exist_ok=True)
    
    import fitz # PyMuPDF
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    
    mode_text = "Double-Page (Split)" if split_pages else "Single-Page"
    print(f"Processing {num_pages} PDFs in {mode_text} mode...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Pass the split configuration to the worker
        tasks = [(i+1, pdf_path, temp_dir, split_pages) for i in range(num_pages)]
        
        with mp.Pool(processes=min(mp.cpu_count(), 4)) as pool:
            # Flatten results list (since each task now returns a list of pages)
            nested_results = pool.map(process_page, tasks)
            flat_results = [item for sublist in nested_results for item in sublist]
        
        # Save results
        output_file = os.path.join(output_dir, "amharic_ocr_output.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            # Sort naturally: 1a, 1b, 2a, 2b...
            for result in flat_results:
                f.write(f"=== Page {result['page']} ===\n")
                f.write(result['text'] + "\n\n")
        
        print(f"✅ OCR complete: {output_file}")

if __name__ == "__main__":
    # CHANGE THIS: Set split_pages=True for your specific file
    main(
        pdf_path="/home/dev1/p.i.s.f/books/books/fiker_split/page_005.pdf", 
        split_pages=True 
    )