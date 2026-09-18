"""
Server runner for the Amharic OCR API.
"""

import uvicorn


def run_server(host: str = "0.0.0.0", port: int = 8023, reload: bool = False):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8023)
        reload: Enable auto-reload for development (default: False)
    """
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run_server(reload=True)
