from pathlib import Path

from src.tools.file_readers.base_reader import BaseFileReader

class ImageReader(BaseFileReader):
    def __init__(self, vision_service=None):
        self._vision = vision_service

    @property
    def name(self) -> str:
        return "image_reader"

    @property
    def description(self) -> str:
        return "Extract metadata from image files (resolution, format, EXIF, vision description)."

    @property
    def supported_extensions(self) -> list[str]:
        return [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]

    def read(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
        except ImportError:
            raise ImportError("Pillow is required to read images. Install with: pip install Pillow")

        img = Image.open(str(path))
        lines = [
            f"Image File: {path.name}",
            f"Format: {img.format}",
            f"Mode: {img.mode}",
            f"Size: {img.width} x {img.height}",
        ]

        exif_data = img._getexif()
        if exif_data:
            lines.append("EXIF:")
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                lines.append(f"  {tag_name}: {value}")

        img.close()

        # Add vision description if available
        if self._vision and self._vision.available:
            try:
                result = self._vision.analyze(file_path)
                if result.description:
                    lines.append(f"\nDescription: {result.description}")
                if result.ocr_text:
                    lines.append(f"OCR Text: {result.ocr_text}")
            except Exception:
                pass

        return "\n".join(lines)
