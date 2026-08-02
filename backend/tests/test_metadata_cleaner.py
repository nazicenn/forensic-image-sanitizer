import pytest
import os
from PIL import Image
from app.services.forensic_cleaner import MetadataCleaner


class TestMetadataCleaner:
    """Test MetadataCleaner class."""

    def setup_method(self):
        self.cleaner = MetadataCleaner()

    def test_cleaner_init(self):
        """Test MetadataCleaner initialization."""
        assert self.cleaner is not None
        assert 'JPEG' in self.cleaner.supported_formats
        assert 'PNG' in self.cleaner.supported_formats

    def test_clean_jpeg(self, tmp_path):
        """Test JPEG metadata cleaning."""
        # Create a test JPEG
        img = Image.new('RGB', (100, 100), color='red')
        test_path = tmp_path / "test.jpg"
        img.save(test_path, 'JPEG', quality=95)

        # Clean metadata
        result = self.cleaner.clean_all(str(test_path))

        assert result is not None
        assert len(result) > 0

    def test_clean_png(self, tmp_path):
        """Test PNG metadata cleaning."""
        # Create a test PNG
        img = Image.new('RGB', (100, 100), color='red')
        test_path = tmp_path / "test.png"
        img.save(test_path, 'PNG')

        # Clean metadata
        result = self.cleaner.clean_all(str(test_path))

        assert result is not None
        assert len(result) > 0

    def test_clean_gps_extraction(self, tmp_path):
        """Test GPS extraction."""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        test_path = tmp_path / "test_gps.jpg"
        img.save(test_path, 'JPEG')

        # Extract GPS (should be empty)
        gps = self.cleaner.clean_gps(str(test_path))
        assert gps == {} or gps is not None