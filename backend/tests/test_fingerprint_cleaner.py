import pytest
import numpy as np
from app.services.forensic_cleaner import FingerprintCleaner


class TestFingerprintCleaner:
    """Test FingerprintCleaner class."""

    def setup_method(self):
        self.cleaner = FingerprintCleaner()

    def test_cleaner_init(self):
        """Test FingerprintCleaner initialization."""
        assert self.cleaner is not None
        assert 'JPEG' in self.cleaner.supported_formats

    def test_clean_all(self):
        """Test cleaning all fingerprints."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.clean_all(image)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_detect_fingerprint(self):
        """Test fingerprint detection."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.detect_fingerprint(image)

        assert 'has_fingerprint' in result
        assert 'metrics' in result
        assert 'confidence' in result

    def test_remove_gan_fingerprint(self):
        """Test GAN fingerprint removal."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.remove_gan_fingerprint(image.astype(np.float32) / 255.0)

        assert result is not None
        assert result.shape == image.shape

    def test_remove_diffusion_fingerprint(self):
        """Test Diffusion fingerprint removal."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.remove_diffusion_fingerprint(image.astype(np.float32) / 255.0)

        assert result is not None
        assert result.shape == image.shape

    def test_rgb_ycbcr_conversion(self):
        """Test RGB to YCbCr conversion."""
        image = np.random.rand(100, 100, 3).astype(np.float32)
        ycbcr = self.cleaner._rgb_to_ycbcr(image)
        assert ycbcr.shape == image.shape

        rgb = self.cleaner._ycbcr_to_rgb(ycbcr)
        assert rgb.shape == image.shape