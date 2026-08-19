"""
Main execution pipeline for Amharic OCR with focused numeral recognition.
"""

import os
import multiprocessing as mp
import pytesseract
from typing import List, Dict, Any, Callable

from .config import OCRConfig
from .constants import ALL_ETHIOPIC_NUMERALS
from .io.pdf_reader import get_page_count, render_page_to_numpy
from .io.output_writer import save_text_output, save_json_output, generate_review_report
from .preprocessing.page_split import split_image_horizontally
from .preprocessing.image_prep import deskew, detect_if_numeral_heavy
from .engines.tesseract import TesseractEngine
from .fusion.combiner import OCRResultCombiner
from .postprocessing.corrections import post_process_text, extract_ethiopic_numerals

def process_single_page(args) -> List[Dict[str, Any]]:
    """
    Worker function to process a single page of the PDF.
    Returns a list of page result dicts (multiple if split_pages is enabled).
    """
    page_num, pdf_path, config = args
    results = []
    
    try:
        # 1. Render PDF page to image at high DPI (400)
        img = render_page_to_numpy(pdf_path, page_num, dpi=config.dpi)
        
        # 2. Split image horizontally if requested (double page scans)
        if config.split_pages:
            sub_images = split_image_horizontally(img)
            page_segments = [('a', sub_images[0]), ('b', sub_images[1])]
        else:
            page_segments = [('', img)]
            
        for suffix, sub_img in page_segments:
            # 3. Deskew image for better alignment
            sub_img_deskewed = deskew(sub_img)
            
            # 4. Detect if image contains mostly numerals
            is_numeral_heavy = detect_if_numeral_heavy(sub_img_deskewed)
            
            engine_outputs = []
            
            # 5. Run Tesseract engine (with multi-PSM numeral fallback)
            if config.use_tesseract:
                tess = TesseractEngine()
                t_res = tess.recognize(sub_img_deskewed, config)
                engine_outputs.append(t_res)
                
            # 6. Run EasyOCR engine if enabled
            if config.use_easyocr:
                from .engines.easyocr_engine import EasyOCREngine
                easy = EasyOCREngine()
                e_res = easy.recognize(sub_img_deskewed, config)
                engine_outputs.append(e_res)
                
            # 7. Combine results from engines
            combined_result = OCRResultCombiner.combine(engine_outputs, strategy="confidence")
            
            # 8. Post-processing corrections
            final_text = post_process_text(combined_result.text, is_numeral_heavy=is_numeral_heavy)
            
            # 9. Extract numerals
            numerals_found = extract_ethiopic_numerals(final_text)
            
            # 10. Error detection and page flagging
            flagged = False
            reasons = []
            
            # Low confidence check
            if combined_result.confidence != -1.0 and combined_result.confidence < 0.6:
                flagged = True
                reasons.append(f"Low confidence ({combined_result.confidence:.2f})")
                
            # Low character count check
            text_len = len(final_text.strip())
            if text_len < config.min_char_threshold:
                flagged = True
                reasons.append(f"Low character count ({text_len} chars)")
                
            # Empty / Error check
            if not final_text.strip() or "[ERROR" in final_text or "[Tesseract Error" in final_text:
                flagged = True
                reasons.append("Empty output or engine error")
                
            results.append({
                'page': f"{page_num}{suffix}",
                'text': final_text,
                'confidence': combined_result.confidence,
                'engine_name': combined_result.engine_name,
                'numeral_heavy': is_numeral_heavy,
                'numerals_found': numerals_found,
                'flagged': flagged,
                'review_reasons': reasons
            })
            
    except Exception as e:
        results.append({
            'page': str(page_num),
            'text': f"[ERROR: Page processing failed: {e}]",
            'confidence': 0.0,
            'engine_name': "pipeline",
            'numeral_heavy': False,
            'numerals_found': [],
            'flagged': True,
            'review_reasons': [f"Fatal processing error: {e}"]
        })
        
    return results

def run_pipeline(pdf_path: str, config: OCRConfig = None, status_callback: Callable[[int, int], None] = None) -> List[Dict[str, Any]]:
    """
    Main entry point for running the extraction pipeline on a PDF file.
    """
    if config is None:
        config = OCRConfig()
        
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Check available languages
    try:
        langs = pytesseract.get_languages()
        print(f"Available languages: {langs}")
        if 'amh' not in langs:
            print("⚠️  Warning: 'amh' language pack not found!")
            print("   Install with: sudo apt-get install tesseract-ocr-amh")
    except Exception as e:
        print(f"Could not check languages: {e}")
        
    num_pages = get_page_count(pdf_path)
    
    print(f"\nProcessing '{os.path.basename(pdf_path)}' ({num_pages} pages)...")
    print(f"Ethiopic numerals in whitelist: {ALL_ETHIOPIC_NUMERALS}")
    print("-" * 50)
    
    tasks = [(i + 1, pdf_path, config) for i in range(num_pages)]
    all_results = []
    
    # If multiprocessing pool is used
    max_workers = min(mp.cpu_count(), 4) if config.use_easyocr else min(mp.cpu_count(), 8)
    
    if num_pages == 1:
        # Avoid process pool overhead for single-page jobs
        page_results = process_single_page(tasks[0])
        all_results.extend(page_results)
        for r in page_results:
            print(f"  Page {r['page']}: Text length: {len(r['text'])} chars | Numerals found: {r['numerals_found']}")
    else:
        with mp.Pool(processes=max_workers) as pool:
            for idx, page_results in enumerate(pool.imap(process_single_page, tasks)):
                all_results.extend(page_results)
                for r in page_results:
                    print(f"  Page {r['page']}/{num_pages}: Text length: {len(r['text'])} chars | Numerals found: {r['numerals_found']}")
                if status_callback:
                    status_callback(idx + 1, num_pages)
                    
    # Define output files
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_out = os.path.join(config.output_dir, f"{base_name}_output.txt")
    json_out = os.path.join(config.output_dir, f"{base_name}_output.json")
    report_out = os.path.join(config.output_dir, f"{base_name}_review_report.txt")
    
    # Save outputs
    save_text_output(all_results, txt_out)
    save_json_output(all_results, json_out)
    generate_review_report(all_results, report_out)
    
    total_numerals = sum(len(r['numerals_found']) for r in all_results)
    
    print("\n" + "=" * 50)
    print(f"✅ OCR complete: {txt_out}")
    print(f"📊 Total numerals detected: {total_numerals}")
    print(f"📄 Structured JSON: {json_out}")
    print(f"📋 Review Report: {report_out}")
    print("=" * 50)
    
    return all_results
