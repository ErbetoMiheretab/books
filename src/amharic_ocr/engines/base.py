from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import numpy as np

@dataclass
class OCRResult:
    text: str
    confidence: float  # Scale of 0.0 to 1.0 (or -1.0 if not supported by engine)
    engine_name: str
    metadata: dict = field(default_factory=dict)

class OCREngine(ABC):
    @abstractmethod
    def recognize(self, image: np.ndarray, config) -> OCRResult:
        """
        Run OCR engine on preprocessed numpy image.
        Returns an OCRResult object.
        """
        pass
