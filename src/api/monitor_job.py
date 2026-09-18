#!/usr/bin/env python3
"""
Monitor OCR job progress in real-time.
"""

import sys
import time
import requests


def monitor_job(job_id: str, base_url: str = "http://localhost:8023", interval: int = 5):
    """
    Monitor a job's progress in real-time.
    
    Args:
        job_id: Job identifier to monitor
        base_url: API base URL
        interval: Polling interval in seconds
    """
    print(f"Monitoring job: {job_id}")
    print(f"API URL: {base_url}")
    print(f"Polling every {interval} seconds...")
    print("=" * 60)
    
    last_pages = 0
    
    while True:
        try:
            # Get status
            response = requests.get(f"{base_url}/ocr/{job_id}/status")
            
            if response.status_code == 404:
                print("❌ Job not found!")
                break
                
            status_data = response.json()
            status = status_data.get("status")
            
            # Get partial results
            results_response = requests.get(f"{base_url}/ocr/{job_id}/results?include_partial=true")
            
            if results_response.status_code == 200:
                results_data = results_response.json()
                pages_processed = results_data.get("pages_processed", 0)
                total_pages = results_data.get("total_pages", "?")
                
                # Show progress if pages increased
                if pages_processed > last_pages:
                    print(f"\r⏳ Status: {status} | Pages: {pages_processed}/{total_pages}", end="", flush=True)
                    
                    # Show latest page details
                    if results_data.get("pages"):
                        latest = results_data["pages"][-1]
                        print(f"\n   Latest: Page {latest['page']}, {latest['text_length']} chars, conf: {latest['confidence']:.2f}")
                    
                    last_pages = pages_processed
            
            # Check if completed or failed
            if status == "completed":
                print("\n\n✅ Job completed!")
                print(f"Total pages: {status_data.get('total_pages')}")
                print(f"Total numerals: {status_data.get('total_numerals')}")
                break
            elif status == "failed":
                print(f"\n\n❌ Job failed: {status_data.get('error')}")
                break
                
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(interval)
    
    print("=" * 60)
    print(f"\nTo get results:")
    print(f"  Text:   curl {base_url}/ocr/{job_id}/text -o output.txt")
    print(f"  JSON:   curl {base_url}/ocr/{job_id}/json -o output.json")
    print(f"  Review: curl {base_url}/ocr/{job_id}/review -o review.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python monitor_job.py <job_id> [base_url] [interval]")
        print("Example: python monitor_job.py abc-123-def http://localhost:8023 5")
        sys.exit(1)
    
    job_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8023"
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    monitor_job(job_id, base_url, interval)
