"""
Command-line interface for Amharic OCR with Ethiopic Numeral Recognition.
"""

import argparse
import os
import sys

from amharic_ocr.config import OCRConfig
from amharic_ocr.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Amharic OCR pipeline with focused Ethiopic numeral recognition."
    )
    
    parser.add_argument(
        "input_pdf",
        nargs="?",
        default=None,
        help="Path to input PDF file (can also be passed with -i/--input)"
    )
    
    parser.add_argument(
        "-i", "--input",
        dest="input_opt",
        help="Path to input PDF file"
    )
    
    parser.add_argument(
        "-o", "--output-dir", 
        default="output_texts",
        help="Directory to save output files (default: output_texts)"
    )
    
    parser.add_argument(
        "--dpi", 
        type=int, 
        default=400,
        help="DPI for converting PDF pages to images (default: 400)"
    )
    
    parser.add_argument(
        "--split", 
        action="store_true",
        help="Split double-page scans horizontally (default: False)"
    )
    
    parser.add_argument(
        "--no-tesseract", 
        action="store_true",
        help="Disable Tesseract OCR engine"
    )
    
    parser.add_argument(
        "--use-easyocr", 
        action="store_true",
        help="Enable EasyOCR fallback engine (default: False)"
    )
    
    parser.add_argument(
        "--gpu", 
        action="store_true",
        help="Enable GPU for EasyOCR if installed (default: False)"
    )
    
    parser.add_argument(
        "--min-char", 
        type=int, 
        default=50,
        help="Minimum character threshold for review flagging (default: 50)"
    )
    
    parser.add_argument(
        "--diagnose", 
        action="store_true",
        help="Run environment setup diagnostics and language checks"
    )
    
    parser.add_argument(
        "--test-numerals",
        action="store_true",
        help="Run synthetic Ethiopic numeral recognition test"
    )

    parser.add_argument(
        "--sauvola",
        action="store_true",
        help="Enable local Sauvola thresholding for image preprocessing (default: False)"
    )

    args = parser.parse_args()

    if args.diagnose:
        from .diagnostics import check_system_setup
        check_system_setup()
        sys.exit(0)

    if args.test_numerals:
        from .diagnostics import test_numeral_recognition
        test_numeral_recognition()
        sys.exit(0)

    pdf_file = args.input_opt or args.input_pdf
    if not pdf_file:
        parser.print_help()
        print("\nError: Please specify a PDF file to process.")
        sys.exit(1)

    if not os.path.exists(pdf_file):
        print(f"Error: File not found: {pdf_file}")
        sys.exit(1)

    # Initialize configuration
    config = OCRConfig(
        dpi=args.dpi,
        split_pages=args.split,
        use_tesseract=not args.no_tesseract,
        use_easyocr=args.use_easyocr,
        easyocr_gpu=args.gpu,
        min_char_threshold=args.min_char,
        output_dir=args.output_dir,
        use_sauvola=args.sauvola
    )


    if not config.use_tesseract and not config.use_easyocr:
        print("Error: You cannot disable all OCR engines.")
        sys.exit(1)

    try:
        run_pipeline(pdf_file, config)
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"Error running pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
