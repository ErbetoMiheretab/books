# Use Tesseract but add preprocessing pipeline for "high accuracy"
import cv2
import numpy as np
import pytesseract
from scipy.ndimage import interpolation

class HighAccuracyAmharicOCR:
    def __init__(self):
        self.lang = 'amh'
    
    def deskew(self, image):
        # Fix rotation for better accuracy
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)
        return rotated
    
    def remove_noise(self, image):
        return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    
    def process(self, image_path):
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        img = self.deskew(img)
        img = self.remove_noise(img)
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Tesseract with optimal config for Amharic
        config = '--psm 6 -c tessedit_char_whitelist=፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼አቡቢባቤብቦቧነንኒናኔንኖኗመሙሚማሜምሞሟ...'
        text = pytesseract.image_to_string(img, lang=self.lang, config=config)
        return text


from paddleocr import PaddleOCR

# Use their multilingual model (supports 80+ languages, may include Amharic-like scripts)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='latin',  # or 'arabic' (similar script characteristics)
    use_gpu=False,
    enable_mkldnn=True  # Intel CPU acceleration
)

result = ocr.ocr('amharic_page.png', cls=True)
for line in result[0]:
    print(line[1][0])