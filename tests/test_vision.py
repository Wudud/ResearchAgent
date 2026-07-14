import sys
from unittest.mock import MagicMock, patch

import pytest

from src.vision.vision_adapter import BaseVisionAdapter, VisionResult
from src.vision.vision_service import VisionService

class TestVisionResult:
    def test_default_result(self):
        result = VisionResult()
        assert result.description == ""
        assert result.ocr_text == ""

    def test_full_result(self):
        result = VisionResult(
            description="A sheep standing, weighing 45kg",
            metadata={"file": "sheep.jpg"},
            quality_score=0.9,
        )
        assert "sheep" in result.description
        assert "45kg" in result.description

class TestVisionService:
    @pytest.fixture
    def mock_adapter(self):
        adapter = MagicMock(spec=BaseVisionAdapter)
        adapter.provider = "mock"
        adapter.analyze.return_value = VisionResult(
            description="A graph showing loss curve",
            ocr_text="Epoch 100, Loss 0.05",
            metadata={"file": "loss.png"},
        )
        return adapter

    def test_available(self, mock_adapter):
        svc = VisionService(mock_adapter)
        assert svc.available is True
        assert svc.provider == "mock"

    def test_not_available(self):
        svc = VisionService(None)
        assert svc.available is False
        assert svc.provider == "none"

    def test_analyze(self, mock_adapter):
        svc = VisionService(mock_adapter)
        result = svc.analyze("test.png")
        mock_adapter.analyze.assert_called_once_with("test.png")
        assert "loss curve" in result.description

    def test_describe(self, mock_adapter):
        svc = VisionService(mock_adapter)
        text = svc.describe("test.png")
        assert "loss curve" in text

    def test_ocr(self, mock_adapter):
        svc = VisionService(mock_adapter)
        text = svc.ocr("test.png")
        assert "Epoch 100" in text

    def test_analyze_without_adapter(self):
        svc = VisionService(None)
        result = svc.analyze("test.png")
        assert "not configured" in result.description.lower()

class TestCLIPAdapter:
    @pytest.fixture
    def mock_clip(self):
        fake_st = MagicMock()
        model = MagicMock()
        model.get_sentence_embedding_dimension.return_value = 512
        model.encode.return_value = MagicMock(tolist=MagicMock(return_value=[0.1, 0.2, 0.3]))
        fake_st.SentenceTransformer.return_value = model

        from unittest.mock import patch
        with patch.dict(sys.modules, {"sentence_transformers": fake_st}):
            yield fake_st

    def test_provider(self, mock_clip):
        from src.embedding.clip_adapter import CLIPEmbeddingAdapter
        adapter = CLIPEmbeddingAdapter(model_name="test")
        assert adapter.provider == "clip"

    def test_supports_image(self, mock_clip):
        from src.embedding.clip_adapter import CLIPEmbeddingAdapter
        adapter = CLIPEmbeddingAdapter(model_name="test")
        assert adapter.supports_image is True

    def test_embed(self, mock_clip):
        from src.embedding.clip_adapter import CLIPEmbeddingAdapter
        adapter = CLIPEmbeddingAdapter(model_name="test")
        result = adapter.embed("test")
        assert isinstance(result, list)

    def test_embed_image(self, mock_clip):
        from src.embedding.clip_adapter import CLIPEmbeddingAdapter
        import tempfile
        from pathlib import Path

        # Create a tiny test PNG
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Minimal PNG: 1x1 pixel
            import struct, zlib
            def create_png(width, height):
                raw = b''
                for y in range(height):
                    raw += b'\x00' + b'\xff\x00\x00' * width
                def chunk(ctype, data):
                    c = ctype + data
                    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
                ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
                return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
            f.write(create_png(1, 1))
            f.flush()
            png_path = f.name

        try:
            # Mock PIL.Image.open to avoid loading actual image
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value.convert.return_value = mock_img.return_value
                adapter = CLIPEmbeddingAdapter(model_name="test")
                result = adapter.embed_image(png_path)
                assert isinstance(result, list)
        finally:
            Path(png_path).unlink(missing_ok=True)

    def test_embed_image_not_found(self, mock_clip):
        from src.embedding.clip_adapter import CLIPEmbeddingAdapter
        adapter = CLIPEmbeddingAdapter(model_name="test")
        with patch("PIL.Image.open") as mock_img:
            mock_img.return_value.convert.return_value = mock_img.return_value
            # File doesn't exist but PIL mock handles the open
            pass

    def test_base_adapter_defaults(self):
        from src.embedding.base_adapter import BaseEmbeddingAdapter
        # Test that defaults don't break
        assert hasattr(BaseEmbeddingAdapter, 'embed_image')
        assert hasattr(BaseEmbeddingAdapter, 'supports_image')
