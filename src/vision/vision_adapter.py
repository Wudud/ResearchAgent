from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class VisionResult:
    description: str = ""           # Image caption / description
    ocr_text: str = ""             # Extracted text (OCR)
    metadata: dict = field(default_factory=dict)   # EXIF, resolution etc.
    quality_score: float = 1.0     # Image quality assessment

class BaseVisionAdapter(ABC):
    @abstractmethod
    def analyze(self, image_path: str) -> VisionResult:
        ...

    @property
    @abstractmethod
    def provider(self) -> str:
        ...
