import pytest
import numpy as np
from PIL import Image
from app.services.forensic_cleaner import StealthCleaner


class TestStealthCleaner:
    """Test StealthCleaner class."""

    def setup_method(self):
        self.cleaner = StealthCleaner()

    def test_cleaner_init(self):
        """Test StealthCleaner initialization."""
        assert self.cleaner is not None
        assert len(self.cleaner.cameras) > 0
        assert len(self.cleaner.edit_software) > 0

    def test_clean_all(self):
        """Test stealth mode application."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.clean_all(image)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_add_jpeg_artifacts(self):
        """Test JPEG artifact addition."""
        pil_image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        result = self.cleaner._add_jpeg_artifacts(pil_image)

        assert result is not None
        assert isinstance(result, Image.Image)

    def test_generate_metadata(self):
        """Test metadata generation."""
        metadata = self.cleaner._generate_metadata()
        assert metadata is not None
        assert metadata.make in ['Canon', 'Nikon', 'Sony', 'Fujifilm', 'Panasonic', 'Apple', 'Google']

    def test_generate_edit_history(self):
        """Test edit history generation."""
        history = self.cleaner._generate_edit_history()
        assert history is not None
        assert history.software in self.cleaner.edit_software
        assert len(history.edits) > 0

    def test_hide_cleaning_traces(self):
        """Test trace hiding."""
        pil_image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        result = self.cleaner._hide_cleaning_traces(pil_image)

        assert result is not None
        assert isinstance(result, Image.Image)

    def test_add_natural_noise(self):
        """Test natural noise addition."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner._add_natural_noise(image)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_generate_gps(self):
        """Test GPS generation."""
        gps = self.cleaner.generate_gps()
        assert 'latitude' in gps
        assert 'longitude' in gps
        assert -90 <= gps['latitude'] <= 90
        assert -180 <= gps['longitude'] <= 180

    def test_get_camera_list(self):
        """Test camera list."""
        cameras = self.cleaner.get_camera_list()
        assert len(cameras) > 0
        assert any('Canon' in cam for cam in cameras)

    def test_get_camera_metadata(self):
        """Test camera metadata retrieval."""
        metadata = self.cleaner.get_camera_metadata('Canon EOS 5D Mark IV')
        if metadata:
            assert metadata.make == 'Canon'
            assert metadata.model == 'EOS 5D Mark IV'

    def test_clean_all_with_camera(self):
        """Test stealth with specific camera."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.cleaner.clean_all(image, camera_name='Nikon D850')

        assert result is not None
        assert result.shape == image.shape