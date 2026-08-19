"""
Image preprocessing routines for Amharic text and Ethiopic numeral OCR.
"""

import cv2
import numpy as np

def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Helper to convert BGR/RGB to Grayscale."""
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image.copy()

def deskew(image: np.ndarray) -> np.ndarray:
    """
    Fix image skew/rotation for better OCR alignment.
    Expects grayscale or BGR/RGB image.
    """
    gray = to_grayscale(image)
    # Threshold to binary for minAreaRect to detect text orientation
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return image
        
    angle = cv2.minAreaRect(coords)[-1]
    
    # minAreaRect returns angle in range [-90, 0)
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    # Only deskew if rotation angle is reasonable (avoids 90 degree flip)
    if abs(angle) > 20:
        return image
        
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess_for_numerals(image: np.ndarray) -> np.ndarray:
    """
    Specialized preprocessing for Ethiopic numeral recognition.
    Numerals need gentler processing than text:
    - Resize small images if min dimension < 50
    - Non-local means denoising
    - Adaptive Gaussian thresholding
    - Morphological closing to connect broken numeral strokes
    """
    gray = to_grayscale(image)
    
    # Resize small images (numerals need sufficient resolution)
    height, width = gray.shape
    min_dim = min(height, width)
    if min_dim < 50:
        scale = 100 / min_dim
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Mild denoising
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Adaptive thresholding preserves numeral details better than Otsu
    binary = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        15, 10
    )
    
    # Morphological closing to connect broken numeral strokes
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return binary

def preprocess_for_text(image: np.ndarray) -> np.ndarray:
    """
    Standard preprocessing for Amharic text:
    - Grayscale conversion
    - Median blur denoising
    - Otsu thresholding
    """
    gray = to_grayscale(image)
    
    # Denoising
    denoised = cv2.medianBlur(gray, 5)
    
    # Otsu thresholding for text
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def detect_if_numeral_heavy(image: np.ndarray) -> bool:
    """
    Heuristic to detect if image contains mostly numerals/sparse structures.
    Based on connected component counts and aspect ratios.
    """
    gray = to_grayscale(image)
    h, w = gray.shape[:2]
    
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    
    small_components = sum(1 for i in range(1, num_labels) 
                           if stats[i, cv2.CC_STAT_WIDTH] < w * 0.1 and stats[i, cv2.CC_STAT_HEIGHT] < h * 0.1)
    
    return small_components > 20
