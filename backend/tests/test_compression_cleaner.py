import pytest
import numpy as np
from PIL import Image
from app.services.forensic_cleaner import CompressionCleaner


class TestCompressionCleaner:
    """Test CompressionCleaner class."""

    def setup_method(self):
        self.cleaner = CompressionCleaner()

    def test_cleaner_init(self):
        """Test CompressionCleaner initialization."""
        assert self.cleaner is not None
        assert 'JPEG' in self.cleaner.supported_formats
        assert len(self.cleaner.quality_levels) > 0

    def test_clean_all(self):
        """Test cleaning compression artifacts."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.clean_all(image, quality=90)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_reencode(self):
        """Test re-encoding."""
        image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        result = self.cleaner._reencode(image, quality=85)

        assert result is not None
        assert isinstance(result, Image.Image)

    def test_resample(self):
        """Test resampling."""
        image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        result = self.cleaner._resample(image, scale=0.95)

        assert result is not None
        assert isinstance(result, Image.Image)

    def test_format_chain(self):
        """Test format chain."""
        image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        result = self.cleaner._format_chain(image)

        assert result is not None
        assert isinstance(result, Image.Image)

    def test_detect_compression(self):
        """Test compression detection."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.detect_compression(image)

        assert 'has_compression_artifacts' in result
        assert 'metrics' in result
        assert 'confidence' in result

    def test_apply_subsampling(self):
        """Test chroma subsampling."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Test 4:4:4 (no subsampling)
        result_444 = self.cleaner.apply_subsampling(image, '4:4:4')
        assert result_444.shape == image.shape

        # Test 4:2:2
        result_422 = self.cleaner.apply_subsampling(image, '4:2:2')
        assert result_422.shape == image.shape

        # Test 4:2:0
        result_420 = self.cleaner.apply_subsampling(image, '4:2:0')
        assert result_420.shape == image.shape

    def test_get_format_chain(self):
        """Test getting format chain."""
        chain = self.cleaner.get_format_chain()
        assert len(chain) > 0
        assert 'JPEG' in chain

    def test_get_quality_levels(self):
        """Test getting quality levels."""
        levels = self.cleaner.get_quality_levels()
        assert len(levels) > 0
        assert 95 in levels