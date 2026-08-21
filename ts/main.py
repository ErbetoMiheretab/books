import cv2
import numpy as np
from PIL import Image


def render_page_to_numpy(pdf_path: str, page_num: int, dpi: int = 400) -> np.ndarray:
    """
    Renders a specific PDF page (1-indexed) to a NumPy BGR image.

    Args:
        pdf_path: Path to PDF file.
        page_num: 1-indexed page number.
        dpi: Target DPI (default: 400).
    """
    try:
        import fitz

        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num - 1)

        # Standard screen DPI is 72. Zoom factor = target_dpi / 72.0
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        # Render page to Pixmap
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return cv_img
    except Exception:  # noqa: BLE001
        # Fallback to pdf2image
        from pdf2image import convert_from_path

        images = convert_from_path(
            pdf_path, first_page=page_num, last_page=page_num, dpi=dpi
        )
        if not images:
            raise ValueError(f"Could not convert page {page_num} of {pdf_path}")
        return cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)


if __name__ == "__main__":
    pdf_file = "ts/page_002.pdf"  
    page_number = 1  # first page
    output_file = f"page_{page_number}.png"
    img = render_page_to_numpy(pdf_file, page_number)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("page_1_gray.png", gray)


    print(f"Saved page {page_number} as {output_file}")
