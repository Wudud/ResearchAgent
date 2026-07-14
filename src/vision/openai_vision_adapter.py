import base64
import logging
from pathlib import Path

import openai

from src.vision.vision_adapter import BaseVisionAdapter, VisionResult

class OpenAIVisionAdapter(BaseVisionAdapter):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o"):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._logger = logging.getLogger("ResearchAgent.OpenAIVisionAdapter")

    @property
    def provider(self) -> str:
        return "openai_vision"

    def analyze(self, image_path: str) -> VisionResult:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        ext = path.suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                     ".gif": "image/gif", ".webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/png")

        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        data_url = f"data:{mime_type};base64,{image_data}"

        description = self._generate_description(data_url, mime_type)
        ocr_text = self._extract_text(data_url, mime_type)

        return VisionResult(
            description=description,
            ocr_text=ocr_text,
            metadata={"file": path.name, "format": ext.lstrip(".")},
        )

    def _generate_description(self, data_url: str, mime_type: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }],
                max_tokens=300,
                temperature=0.1,
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as e:
            self._logger.warning(f"Vision description failed: {e}")
            return ""

    def _extract_text(self, data_url: str, mime_type: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }],
                max_tokens=500,
                temperature=0.0,
            )
            text = response.choices[0].message.content or ""
            return "" if text.strip() == "NONE" else text
        except openai.OpenAIError as e:
            self._logger.warning(f"Vision OCR failed: {e}")
            return ""
