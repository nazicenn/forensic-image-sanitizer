import pytest
import numpy as np
from app.services.sanitizer import ImageSanitizer, CleanLevel


class TestImageSanitizer:
    """Test ImageSanitizer class."""

    def setup_method(self):
        self.sanitizer = ImageSanitizer()

    def test_sanitizer_init(self):
        """Test ImageSanitizer initialization."""
        assert self.sanitizer is not None
        assert len(self.sanitizer.level_settings) == 4

    def test_light_cleaning(self):
        """Test light cleaning level."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.sanitizer.sanitize(image, CleanLevel.LIGHT)

        assert result.success is True
        assert result.image is not None
        assert result.image.shape == image.shape

    def test_medium_cleaning(self):
        """Test medium cleaning level."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.sanitizer.sanitize(image, CleanLevel.MEDIUM)

        assert result.success is True
        assert result.image is not None
        assert 'metadata_cleaned' in result.steps

    def test_aggressive_cleaning(self):
        """Test aggressive cleaning level."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.sanitizer.sanitize(image, CleanLevel.AGGRESSIVE)

        assert result.success is True
        assert result.image is not None
        assert len(result.steps) >= 4

    def test_forensic_cleaning(self):
        """Test forensic cleaning level."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.sanitizer.sanitize(image, CleanLevel.FORENSIC)

        assert result.success is True
        assert result.image is not None
        assert len(result.steps) >= 6

    def test_quality_metrics(self):
        """Test quality metrics calculation."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.sanitizer.sanitize(image, CleanLevel.MEDIUM)

        assert 'quality' in result.metrics
        assert 'ssim' in result.metrics['quality']
        assert 'psnr' in result.metrics['quality']

    def test_batch_sanitize(self):
        """Test batch sanitization."""
        images = [
            np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8),
            np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8),
            np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        ]
        results = self.sanitizer.batch_sanitize(images, CleanLevel.MEDIUM)

        assert len(results) == 3
        assert all(r.success for r in results)

    def test_get_level_settings(self):
        """Test getting level settings."""
        settings = self.sanitizer.get_level_settings(CleanLevel.LIGHT)
        assert settings['metadata'] is True
        assert settings['frequency'] is False

    def test_get_levels(self):
        """Test getting available levels."""
        levels = self.sanitizer.get_levels()
        assert 'light' in levels
        assert 'medium' in levels
        assert 'aggressive' in levels
        assert 'forensic' in levels

    def test_error_handling(self):
        """Test error handling."""
        # Invalid image
        result = self.sanitizer.sanitize(np.array([]), CleanLevel.MEDIUM)
        assert result.success is False
        assert result.error is not None