import pytest
import numpy as np
from app.services.forensic_cleaner import PRNUCleaner


class TestPRNUCleaner:
    """Test PRNUCleaner class."""

    def setup_method(self):
        self.cleaner = PRNUCleaner()

    def test_cleaner_init(self):
        """Test PRNUCleaner initialization."""
        assert self.cleaner is not None
        assert len(self.cleaner.camera_profiles) > 0

    def test_camera_profiles(self):
        """Test camera profiles."""
        profiles = self.cleaner.get_camera_list()
        assert 'canon_5d_mark_iv' in profiles
        assert 'nikon_d850' in profiles
        assert 'sony_a7iii' in profiles

    def test_get_camera_info(self):
        """Test getting camera info."""
        info = self.cleaner.get_camera_info('canon_5d_mark_iv')
        assert info['manufacturer'] == 'Canon'
        assert info['model'] == 'EOS 5D Mark IV'
        assert 'iso_range' in info

    def test_add_prnu(self):
        """Test adding PRNU noise."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.add_prnu(image, 'canon_5d_mark_iv', iso=400)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_add_adaptive_noise(self):
        """Test adaptive noise."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.add_adaptive_noise(image, iso=400)

        assert result is not None
        assert result.shape == image.shape

    def test_generate_prnu_pattern(self):
        """Test PRNU pattern generation."""
        pattern = self.cleaner.generate_prnu_pattern((64, 64), 'canon_5d_mark_iv')
        assert pattern is not None
        assert pattern.shape == (64, 64)

    def test_apply_bayer_pattern(self):
        """Test Bayer pattern application."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8).astype(np.float32) / 255.0
        result = self.cleaner.apply_bayer_pattern(image, 'RGGB')

        assert result is not None
        assert result.shape == image.shape