# Amharic OCR API

FastAPI server providing REST endpoints for Amharic OCR with Ethiopic numeral recognition.

## Features

- **PDF Upload & Processing**: Upload PDF files for OCR processing
- **Multiple Output Formats**: Get results as plain text, structured JSON, or quality review reports
- **Job Tracking**: Monitor processing status with unique job IDs
- **System Diagnostics**: Verify OCR dependencies and system setup
- **Configurable Processing**: Adjust DPI, page splitting, and engine options

## Quick Start

### Installation

```bash
# Install dependencies
pip install -e .
```

### Running the Server

#### Option 1: Using the command-line script
```bash
amharic-ocr-server
```

#### Option 2: Using Python directly
```bash
python -m api.server
```

#### Option 3: Using uvicorn directly
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Root Endpoint
```http
GET /
```
Returns API information and available endpoints.

### 2. Health Check
```http
GET /health
```
Check if the service is running.

### 3. System Diagnostics
```http
GET /diagnostics
```
Run system diagnostics to verify OCR dependencies (Tesseract, language packs, etc.).

### 4. Upload PDF for OCR
```http
POST /ocr
```
Upload a PDF file for processing.

**Parameters:**
- `file` (required): PDF file to process
- `dpi` (optional): Rendering resolution (default: 400)
- `split_pages` (optional): Split double-page scans (default: false)
- `use_easyocr` (optional): Enable EasyOCR engine (default: false)
- `gpu` (optional): Enable GPU for EasyOCR (default: false)
- `min_char_threshold` (optional): Quality threshold (default: 50)

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "message": "OCR processing completed successfully"
}
```

### 5. Get Job Status
```http
GET /ocr/{job_id}/status
```
Check the processing status of a job.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "filename": "example.pdf",
  "files_available": ["text", "json", "review"],
  "total_pages": 10,
  "total_numerals": 42
}
```

### 6. Get Text Output
```http
GET /ocr/{job_id}/text
```
Download the plain text output file.

### 7. Get JSON Output
```http
GET /ocr/{job_id}/json
```
Download the structured JSON output with full metadata.

### 8. Get Review Report
```http
GET /ocr/{job_id}/review
```
Download the quality review report.

### 9. Get Results Summary
```http
GET /ocr/{job_id}/results
```
Get a JSON summary of results with page-level details.

**Response:**
```json
{
  "job_id": "uuid-string",
  "filename": "example.pdf",
  "total_pages": 10,
  "pages": [
    {
      "page": "1",
      "text_length": 1024,
      "confidence": 0.95,
      "engine": "tesseract_amh+eng_psm6",
      "numerals_found": ["፩", "፪", "፫"],
      "flagged": false,
      "review_reasons": []
    }
  ]
}
```

### 10. Delete Job
```http
DELETE /ocr/{job_id}
```
Delete a job and all associated files.

## Usage Examples

### Using cURL

#### Upload a PDF
```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@books/sample.pdf" \
  -F "dpi=400" \
  -F "split_pages=false"
```

#### Check Status
```bash
curl "http://localhost:8000/ocr/{job_id}/status"
```

#### Download Text Output
```bash
curl "http://localhost:8000/ocr/{job_id}/text" -o output.txt
```

### Using Python

```python
import requests

# Upload PDF
with open("books/sample.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/ocr",
        files={"file": f},
        data={"dpi": 400, "split_pages": False}
    )
    
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Check status
status_response = requests.get(f"http://localhost:8000/ocr/{job_id}/status")
print(status_response.json())

# Get results summary
results = requests.get(f"http://localhost:8000/ocr/{job_id}/results")
print(results.json())

# Download text output
text_response = requests.get(f"http://localhost:8000/ocr/{job_id}/text")
with open("output.txt", "wb") as f:
    f.write(text_response.content)
```

## Configuration

### Server Configuration

The server can be configured via environment variables or command-line arguments:

- `HOST`: Host address (default: 0.0.0.0)
- `PORT`: Port number (default: 8000)
- `RELOAD`: Enable auto-reload for development (default: False)

### OCR Configuration

OCR processing options can be specified when uploading PDFs:

- `dpi`: Image resolution (higher = better quality, slower processing)
- `split_pages`: Enable for double-page book scans
- `use_easyocr`: Add EasyOCR as a secondary engine (requires more memory)
- `gpu`: Enable CUDA acceleration for EasyOCR
- `min_char_threshold`: Pages with fewer characters are flagged for review

## Storage

- **Uploads**: Stored in `uploads/` directory
- **Results**: Stored in `results/{job_id}/` directory

Note: In a production environment, consider implementing:
- Persistent storage (database) for job tracking
- File cleanup policies
- Authentication and authorization
- Rate limiting
- Request validation and sanitization

## Development

### Running in Development Mode

```bash
# With auto-reload
python -m api.server
```

### Running Tests

```bash
# Test the API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/diagnostics
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Resource not found (job ID, file)
- `500`: Server error (processing failure)

Error responses include detail messages:
```json
{
  "detail": "Error description"
}
```

## Performance Considerations

- Processing time depends on PDF size, DPI, and page count
- Single-page PDFs are processed without multiprocessing overhead
- Multi-page PDFs use parallel processing (4-8 workers)
- EasyOCR requires significantly more memory and GPU resources
- Consider implementing async job processing for production use

## Security Notes

This is a basic implementation. For production deployment:

1. Add authentication (API keys, OAuth, etc.)
2. Implement rate limiting
3. Sanitize uploaded files
4. Add CORS middleware if needed
5. Use HTTPS
6. Implement file size limits
7. Add request validation
8. Set up proper logging and monitoring
