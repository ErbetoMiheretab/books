# Amharic OCR & Ethiopic Numeral Recognition

A high-accuracy pipeline for scanned and photographed Amharic book extraction with specialized support for the Ethiopic Fidel syllabary and Ethiopic numerals (`፩` – `፼`).

For a comprehensive module-by-module architectural explanation, see [CODEBASE_EXPLANATION.md](file:///home/dev1/p.i.s.f/books/CODEBASE_EXPLANATION.md).

## Quick Start

### Installation

```bash
# Using uv or pip
pip install -e .
```

Ensure system packages are installed:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-amh fonts-noto-ethiopic
```

### Running Diagnostics

```bash
# Verify environment and available language models
amharic-ocr --diagnose

# Run synthetic Ethiopic numeral test
amharic-ocr --test-numerals
```

### Processing a PDF

```bash
# Basic usage
amharic-ocr books/sample.pdf

# Double-page scans with custom output directory
amharic-ocr books/sample.pdf --split -o output_texts
```
