"""
MinIO Storage Client
"""

import io
from minio import Minio
from minio.error import S3Error
from PIL import Image
import numpy as np
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO storage client."""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Ensure bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Bucket {self.bucket} created")
        except Exception as e:
            logger.error(f"Failed to ensure bucket: {e}")

    def save_image(self, filename: str, image: np.ndarray) -> bool:
        """
        Save image to MinIO.

        Args:
            filename: File name
            image: Image as numpy array

        Returns:
            bool: Success
        """
        try:
            # Convert to PIL
            if image.dtype == np.uint8:
                pil_image = Image.fromarray(image)
            else:
                pil_image = Image.fromarray((image * 255).astype(np.uint8))

            # Save to bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=92)
            buffer.seek(0)

            # Upload
            self.client.put_object(
                self.bucket,
                filename,
                buffer,
                length=buffer.getbuffer().nbytes,
                content_type='image/jpeg'
            )

            logger.info(f"Image {filename} saved to MinIO")
            return True

        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return False

    def get_image(self, filename: str) -> np.ndarray:
        """
        Get image from MinIO.

        Args:
            filename: File name

        Returns:
            np.ndarray: Image as numpy array
        """
        try:
            # Get object
            response = self.client.get_object(self.bucket, filename)
            data = response.read()
            response.close()
            response.release_conn()

            # Convert to PIL
            pil_image = Image.open(io.BytesIO(data))
            image = np.array(pil_image)

            logger.info(f"Image {filename} retrieved from MinIO")
            return image

        except S3Error as e:
            logger.error(f"Failed to get image: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get image: {e}")
            return None

    def delete_image(self, filename: str) -> bool:
        """
        Delete image from MinIO.

        Args:
            filename: File name

        Returns:
            bool: Success
        """
        try:
            self.client.remove_object(self.bucket, filename)
            logger.info(f"Image {filename} deleted from MinIO")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            return False

    def get_presigned_url(self, filename: str, expires: int = 3600) -> str:
        """
        Get presigned URL for image.

        Args:
            filename: File name
            expires: Expiration in seconds

        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                filename,
                expires=expires
            )
            return url
        except Exception as e:
            logger.error(f"Failed to get presigned URL: {e}")
            return None