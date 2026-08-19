"""
Output generation for OCR results (Plain Text, JSON metadata, and Quality Review reports).
"""

import os
import json
from typing import List, Dict, Any

def save_text_output(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save text output matching amh_ocr_nums.py structure:
    === Page X ===
    <page_text>
    [Numerals: ፩, ፪, ፫]
    """
    with open(output_path, "w", encoding="utf-8") as f:
        sorted_results = sorted(results, key=lambda x: str(x['page']))
        for result in sorted_results:
            f.write(f"=== Page {result['page']} ===\n")
            f.write(result['text'] + "\n")
            if result.get('numerals_found'):
                f.write(f"[Numerals: {', '.join(result['numerals_found'])}]\n")
            f.write("\n")

def save_json_output(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save structured JSON output with page metadata and detected numerals."""
    serializable = []
    for r in results:
        serializable.append({
            'page': r['page'],
            'text': r['text'],
            'confidence': float(r.get('confidence', 0.0)),
            'engine_name': r.get('engine_name', 'unknown'),
            'numeral_heavy': bool(r.get('numeral_heavy', False)),
            'numerals_found': r.get('numerals_found', []),
            'character_count': len(r.get('text', '')),
            'is_flagged_for_review': bool(r.get('flagged', False)),
            'review_reasons': r.get('review_reasons', [])
        })
        
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

def generate_review_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """Generate quality diagnostic report for flagged pages."""
    flagged_pages = [r for r in results if r.get('flagged', False)]
    total_numerals = sum(len(r.get('numerals_found', [])) for r in results)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("AMHARIC OCR PIPELINE — QUALITY AND REVIEW REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total processed pages: {len(results)}\n")
        f.write(f"Total Ethiopic numerals detected: {total_numerals}\n")
        f.write(f"Pages flagged for review: {len(flagged_pages)}\n\n")
        
        if flagged_pages:
            f.write("FLAGGED PAGES DETAIL:\n")
            f.write("-" * 80 + "\n")
            for r in flagged_pages:
                reasons = ", ".join(r.get('review_reasons', []))
                f.write(f"Page {r['page']}: [Engine: {r.get('engine_name')}] [Confidence: {r.get('confidence', 0.0):.2f}] [Chars: {len(r.get('text', ''))}]\n")
                f.write(f"  -> Reason(s): {reasons}\n")
                snippet = r.get('text', '')[:100].replace('\n', ' ')
                f.write(f"  -> Snippet: {snippet}...\n")
                f.write("-" * 80 + "\n")
        else:
            f.write("🎉 Excellent! No pages triggered the error detection thresholds.\n")
