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

def sauvola_threshold(image: np.ndarray, window_size: int = 15, k: float = 0.2, R: float = 128.0) -> np.ndarray:
    """
    Applies Sauvola local thresholding to a grayscale image.
    T = m * (1 + k * (s / R - 1))
    """
    gray = to_grayscale(image)
    
    # Calculate local mean (m)
    mean = cv2.boxFilter(gray, cv2.CV_32F, (window_size, window_size))
    
    # Calculate local mean of squared image (E[X^2])
    sq_gray = np.square(gray.astype(np.float32))
    sq_mean = cv2.boxFilter(sq_gray, cv2.CV_32F, (window_size, window_size))
    
    # Local variance = E[X^2] - (E[X])^2
    var = sq_mean - np.square(mean)
    var = np.maximum(var, 0)  # Ensure variance is non-negative
    std = np.sqrt(var)
    
    # Compute Sauvola threshold
    threshold = mean * (1.0 + k * (std / R - 1.0))
    
    # Binarize: standard text is black-on-white (foreground is 0, background is 255)
    binary = np.zeros_like(gray)
    binary[gray > threshold] = 255
    
    return binary

def preprocess_for_numerals(image: np.ndarray, use_sauvola: bool = False) -> np.ndarray:
    """
    Specialized preprocessing for Ethiopic numeral recognition.
    Numerals need gentler processing than text:
    - Resize small images if min dimension < 50
    - Non-local means denoising
    - Adaptive Gaussian thresholding or Sauvola local thresholding
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
    
    if use_sauvola:
        binary = sauvola_threshold(denoised)
    else:
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

def preprocess_for_text(image: np.ndarray, use_sauvola: bool = False) -> np.ndarray:
    """
    Standard preprocessing for Amharic text:
    - Grayscale conversion
    - Median blur denoising
    - Otsu thresholding or Sauvola local thresholding
    """
    gray = to_grayscale(image)
    
    # Denoising
    denoised = cv2.medianBlur(gray, 5)
    
    if use_sauvola:
        binary = sauvola_threshold(denoised)
    else:
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
    num_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(binary)
    
    small_components = sum(1 for i in range(1, num_labels) 
                           if stats[i, cv2.CC_STAT_WIDTH] < w * 0.1 and stats[i, cv2.CC_STAT_HEIGHT] < h * 0.1)
    
    return small_components > 20
