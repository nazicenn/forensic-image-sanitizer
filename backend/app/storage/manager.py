"""
Storage Manager - Unified interface for MinIO and Local storage.
"""

import logging
from typing import Optional, Tuple
from datetime import datetime
import numpy as np
from PIL import Image
import io

from app.storage.minio import MinIOClient
from app.storage.local import LocalStorage
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Unified storage manager with automatic fallback.
    """

    def __init__(self):
        self.minio = MinIOClient()
        self.local = LocalStorage()
        self.use_minio = True  # Will fallback to local if MinIO fails

    def save_image(self, filename: str, image: np.ndarray, use_minio: bool = True) -> bool:
        """
        Save image to storage.

        Args:
            filename: File name
            image: Image as numpy array
            use_minio: Try MinIO first

        Returns:
            bool: Success
        """
        # Convert to bytes
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=92)
        data = buffer.getvalue()

        # Try MinIO
        if use_minio and self.use_minio:
            try:
                success = self.minio.save_image(filename, image)
                if success:
                    logger.info(f"Image saved to MinIO: {filename}")
                    return True
            except Exception as e:
                logger.warning(f"MinIO save failed, falling back to local: {e}")

        # Fallback to local
        logger.info(f"Saving image to local storage: {filename}")
        return self.local.save_processed(filename, data)

    def get_image(self, filename: str, use_minio: bool = True) -> Optional[np.ndarray]:
        """
        Get image from storage.

        Args:
            filename: File name
            use_minio: Try MinIO first

        Returns:
            np.ndarray: Image or None
        """
        # Try MinIO
        if use_minio and self.use_minio:
            try:
                image = self.minio.get_image(filename)
                if image is not None:
                    logger.info(f"Image retrieved from MinIO: {filename}")
                    return image
            except Exception as e:
                logger.warning(f"MinIO get failed, trying local: {e}")

        # Try local storage
        logger.info(f"Retrieving image from local storage: {filename}")
        data = self.local.get_processed(filename)

        if data is not None:
            try:
                pil_image = Image.open(io.BytesIO(data))
                return np.array(pil_image)
            except Exception as e:
                logger.error(f"Failed to convert image: {e}")

        return None

    def get_temp_image(self, filename: str) -> Optional[np.ndarray]:
        """Get temporary image."""
        data = self.local.get_temp(filename)

        if data is not None:
            try:
                pil_image = Image.open(io.BytesIO(data))
                return np.array(pil_image)
            except Exception as e:
                logger.error(f"Failed to convert temp image: {e}")

        return None

    def save_temp_image(self, filename: str, image: np.ndarray) -> bool:
        """Save temporary image."""
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=92)
        data = buffer.getvalue()

        return self.local.save_temp(filename, data)

    def archive(self, filename: str) -> bool:
        """Archive file."""
        return self.local.archive(filename)

    def delete(self, filename: str) -> bool:
        """Delete file from all storage."""
        success = True

        # Delete from MinIO
        try:
            self.minio.delete_image(filename)
        except Exception as e:
            logger.warning(f"MinIO delete failed: {e}")

        # Delete from local
        success = self.local.delete(filename) and success

        return success

    def get_presigned_url(self, filename: str, expires: int = 3600) -> Optional[str]:
        """Get presigned URL for download."""
        try:
            return self.minio.get_presigned_url(filename, expires)
        except Exception as e:
            logger.warning(f"Failed to get presigned URL: {e}")
            return None

    def get_file_info(self, filename: str) -> dict:
        """Get file information."""
        info = {
            'filename': filename,
            'exists': False,
            'size': 0,
            'storage': 'none',
            'url': None
        }

        # Check MinIO
        try:
            # Try to get presigned URL (indicates existence)
            url = self.minio.get_presigned_url(filename, expires=60)
            if url:
                info['exists'] = True
                info['storage'] = 'minio'
                info['url'] = url
                return info
        except:
            pass

        # Check local
        size = self.local.get_file_size(filename)
        if size > 0:
            info['exists'] = True
            info['size'] = size
            info['storage'] = 'local'

        return info