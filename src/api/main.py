"""
FastAPI server for Amharic OCR with Ethiopic numeral recognition.

This API provides endpoints to:
- Upload PDF files for OCR processing
- Retrieve OCR results (text, JSON, review reports)
- Check processing status
- Get system diagnostics
"""

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from amharic_ocr.config import OCRConfig
from amharic_ocr.diagnostics import check_system_setup
from amharic_ocr.pipeline import run_pipeline

app = FastAPI(
    title="Amharic OCR API",
    description="High-accuracy OCR service for Amharic text and Ethiopic numerals",
    version="0.1.0",
)

# Directory for storing uploaded PDFs and results
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# In-memory storage for job status (could be replaced with Redis/database)
job_store: dict[str, dict[str, Any]] = {}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Amharic OCR API",
        "version": "0.1.0",
        "description": "OCR service for Amharic text with Ethiopic numeral recognition",
        "endpoints": {
            "POST /ocr": "Upload PDF for OCR processing",
            "GET /ocr/{job_id}/status": "Get processing status",
            "GET /ocr/{job_id}/text": "Get plain text output",
            "GET /ocr/{job_id}/json": "Get structured JSON output",
            "GET /ocr/{job_id}/review": "Get quality review report",
            "GET /health": "Health check",
            "GET /diagnostics": "System diagnostics",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "amharic-ocr"}


@app.get("/diagnostics")
async def diagnostics():
    """Run system diagnostics to verify OCR dependencies."""
    try:
        diagnostics_output = check_system_setup()
        return {"status": "success", "diagnostics": diagnostics_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {str(e)}")


@app.post("/ocr")
async def process_pdf(
    file: UploadFile = File(...),
    dpi: int = 400,
    split_pages: bool = False,
    use_easyocr: bool = False,
    gpu: bool = False,
    min_char_threshold: int = 50,
):
    """
    Upload a PDF file for OCR processing.

    Args:
        file: PDF file to process
        dpi: Rendering resolution (default: 400)
        split_pages: Split double-page scans horizontally (default: False)
        use_easyocr: Enable EasyOCR as secondary engine (default: False)
        gpu: Enable GPU acceleration for EasyOCR (default: False)
        min_char_threshold: Minimum character count for quality flagging (default: 50)

    Returns:
        Job ID for tracking processing status
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    pdf_path = UPLOAD_DIR / f"{job_id}.pdf"
    try:
        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Initialize job status
    job_store[job_id] = {
        "status": "processing",
        "filename": file.filename,
        "pdf_path": str(pdf_path),
        "config": {
            "dpi": dpi,
            "split_pages": split_pages,
            "use_easyocr": use_easyocr,
            "gpu": gpu,
            "min_char_threshold": min_char_threshold,
        },
    }

    # Create output directory for this job
    output_dir = RESULTS_DIR / job_id
    output_dir.mkdir(exist_ok=True)

    # Configure OCR
    config = OCRConfig(
        dpi=dpi,
        split_pages=split_pages,
        use_tesseract=True,
        use_easyocr=use_easyocr,
        easyocr_gpu=gpu,
        min_char_threshold=min_char_threshold,
        output_dir=str(output_dir),
    )

    try:
        # Run OCR pipeline
        results = run_pipeline(str(pdf_path), config)

        # Update job status
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["results"] = results
        job_store[job_id]["output_dir"] = str(output_dir)

        # Get output file paths
        base_name = Path(file.filename).stem
        job_store[job_id]["files"] = {
            "text": str(output_dir / f"{base_name}_output.txt"),
            "json": str(output_dir / f"{base_name}_output.json"),
            "review": str(output_dir / f"{base_name}_review_report.txt"),
        }

    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    return {
        "job_id": job_id,
        "status": job_store[job_id]["status"],
        "message": "OCR processing completed successfully",
    }


@app.get("/ocr/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of an OCR job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"],
    }

    if job["status"] == "completed":
        response["files_available"] = list(job.get("files", {}).keys())
        response["total_pages"] = len(job.get("results", []))
        response["total_numerals"] = sum(
            len(r.get("numerals_found", [])) for r in job.get("results", [])
        )
    elif job["status"] == "failed":
        response["error"] = job.get("error", "Unknown error")

    return response


@app.get("/ocr/{job_id}/text")
async def get_text_output(job_id: str):
    """Get the plain text output of an OCR job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400, detail=f"Job status: {job['status']}. Results not available yet."
        )

    text_file = job["files"]["text"]
    if not os.path.exists(text_file):
        raise HTTPException(status_code=404, detail="Text output file not found")

    return FileResponse(
        text_file, media_type="text/plain", filename=f"{job['filename']}_output.txt"
    )


@app.get("/ocr/{job_id}/json")
async def get_json_output(job_id: str):
    """Get the structured JSON output of an OCR job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400, detail=f"Job status: {job['status']}. Results not available yet."
        )

    json_file = job["files"]["json"]
    if not os.path.exists(json_file):
        raise HTTPException(status_code=404, detail="JSON output file not found")

    return FileResponse(
        json_file,
        media_type="application/json",
        filename=f"{job['filename']}_output.json",
    )


@app.get("/ocr/{job_id}/review")
async def get_review_report(job_id: str):
    """Get the quality review report of an OCR job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400, detail=f"Job status: {job['status']}. Results not available yet."
        )

    review_file = job["files"]["review"]
    if not os.path.exists(review_file):
        raise HTTPException(status_code=404, detail="Review report file not found")

    return FileResponse(
        review_file,
        media_type="text/plain",
        filename=f"{job['filename']}_review_report.txt",
    )


@app.get("/ocr/{job_id}/results")
async def get_results_summary(job_id: str):
    """Get a summary of OCR results with page-level details."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400, detail=f"Job status: {job['status']}. Results not available yet."
        )

    results = job.get("results", [])
    return JSONResponse(
        content={
            "job_id": job_id,
            "filename": job["filename"],
            "total_pages": len(results),
            "pages": [
                {
                    "page": r["page"],
                    "text_length": len(r["text"]),
                    "confidence": r["confidence"],
                    "engine": r["engine_name"],
                    "numerals_found": r["numerals_found"],
                    "flagged": r["flagged"],
                    "review_reasons": r["review_reasons"],
                }
                for r in results
            ],
        }
    )


@app.delete("/ocr/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]

    # Delete PDF file
    pdf_path = Path(job["pdf_path"])
    if pdf_path.exists():
        pdf_path.unlink()

    # Delete output directory
    output_dir = Path(job.get("output_dir", ""))
    if output_dir.exists():
        for file in output_dir.iterdir():
            file.unlink()
        output_dir.rmdir()

    # Remove from job store
    del job_store[job_id]

    return {"message": f"Job {job_id} deleted successfully"}
