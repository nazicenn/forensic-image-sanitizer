import pytest
import numpy as np
from PIL import Image
from app.services.forensic_cleaner import FrequencyCleaner


class TestFrequencyCleaner:
    """Test FrequencyCleaner class."""

    def setup_method(self):
        self.cleaner = FrequencyCleaner()

    def test_cleaner_init(self):
        """Test FrequencyCleaner initialization."""
        assert self.cleaner is not None
        assert 'JPEG' in self.cleaner.supported_formats

    def test_clean_image(self):
        """Test cleaning a simple image."""
        # Create a test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Clean
        cleaned = self.cleaner.clean_all(image)

        assert cleaned is not None
        assert cleaned.shape == image.shape
        assert cleaned.dtype == np.uint8

    def test_detect_checkerboard(self):
        """Test checkerboard detection."""
        image = np.random.randint(0, 255, (64, 64), dtype=np.uint8)

        # Add checkerboard pattern
        for i in range(0, 64, 4):
            for j in range(0, 64, 4):
                if (i // 4 + j // 4) % 2 == 0:
                    image[i:i+4, j:j+4] = 255

        image_float = image.astype(np.float32) / 255.0
        fft_data = np.fft.fft2(image_float)
        result = self.cleaner.detect_checkerboard(fft_data)

        assert 'has_checkerboard' in result
        assert 'peaks' in result

    def test_detect_grid(self):
        """Test grid artifact detection."""
        image = np.random.randint(0, 255, (64, 64), dtype=np.uint8)

        # Add grid
        image[::8, :] = 255
        image[:, ::8] = 255

        image_float = image.astype(np.float32) / 255.0
        fft_data = np.fft.fft2(image_float)
        result = self.cleaner.detect_grid_artifacts(fft_data)

        assert 'has_grid' in result
        assert 'horizontal_peaks' in result

    def test_analyze_spectrum(self):
        """Test spectrum analysis."""
        image = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        image_float = image.astype(np.float32) / 255.0
        fft_data = np.fft.fft2(image_float)
        result = self.cleaner.analyze_spectrum(fft_data)

        assert '1f_slope' in result
        assert 'anomaly_detected' in result

    def test_resample(self):
        """Test resampling."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        resampled = self.cleaner.resample(image, shift=0.3)

        assert resampled is not None
        assert resampled.shape == image.shape