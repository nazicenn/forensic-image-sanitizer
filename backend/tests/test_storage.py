import pytest
import numpy as np
from PIL import Image
from app.storage import LocalStorage, StorageManager


class TestLocalStorage:
    """Test LocalStorage class."""

    def setup_method(self):
        self.storage = LocalStorage()

    def test_init(self):
        """Test LocalStorage initialization."""
        assert self.storage is not None
        assert self.storage.base_path.exists()

    def test_save_temp(self):
        """Test saving temporary file."""
        data = b"test data"
        result = self.storage.save_temp("test.txt", data)
        assert result is True

    def test_get_temp(self):
        """Test getting temporary file."""
        data = b"test data"
        self.storage.save_temp("test_get.txt", data)
        result = self.storage.get_temp("test_get.txt")
        assert result == data

    def test_save_processed(self):
        """Test saving processed file."""
        data = b"test data"
        result = self.storage.save_processed("test_processed.txt", data)
        assert result is True


class TestStorageManager:
    """Test StorageManager class."""

    def setup_method(self):
        self.manager = StorageManager()

    def test_init(self):
        """Test StorageManager initialization."""
        assert self.manager is not None
        assert self.manager.minio is not None
        assert self.manager.local is not None

    def test_save_image(self):
        """Test saving image."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.manager.save_image("test_save.jpg", image)
        assert result is True

    def test_get_image(self):
        """Test getting image."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        self.manager.save_image("test_get.jpg", image)
        result = self.manager.get_image("test_get.jpg")
        assert result is not None
        assert result.shape == image.shape

    def test_get_file_info(self):
        """Test getting file info."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        self.manager.save_image("test_info.jpg", image)
        info = self.manager.get_file_info("test_info.jpg")
        assert info['filename'] == "test_info.jpg"
        assert info['exists'] is True