import cv2
import numpy as np
from typing import List

def split_image_horizontally(image: np.ndarray) -> List[np.ndarray]:
    """
    Splits an image into Left and Right pages.
    Usually used when a PDF page contains two scanned book pages side-by-side.
    """
    h, w = image.shape[:2]
    midpoint = w // 2
    
    # Crop: [Start_Y:End_Y, Start_X:End_X]
    left_page = image[0:h, 0:midpoint]
    right_page = image[0:h, midpoint:w]
    
    return [left_page, right_page]
