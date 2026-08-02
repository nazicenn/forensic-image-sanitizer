"""
Local Storage - Fallback storage when MinIO is unavailable.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalStorage:
    """Local file storage fallback."""

    def __init__(self):
        self.base_path = Path(settings.TEMP_STORAGE_PATH)
        self.processed_path = Path(settings.PROCESSED_STORAGE_PATH)
        self.archive_path = self.base_path / "archive"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.processed_path.mkdir(parents=True, exist_ok=True)
            self.archive_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage directories created at {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")

    def save_temp(self, filename: str, data: bytes) -> bool:
        """Save temporary file."""
        try:
            filepath = self.base_path / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'wb') as f:
                f.write(data)

            logger.info(f"Temp file saved: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save temp file: {e}")
            return False

    def get_temp(self, filename: str) -> Optional[bytes]:
        """Get temporary file."""
        try:
            filepath = self.base_path / filename
            if not filepath.exists():
                logger.warning(f"Temp file not found: {filepath}")
                return None

            with open(filepath, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to get temp file: {e}")
            return None

    def save_processed(self, filename: str, data: bytes) -> bool:
        """Save processed file."""
        try:
            filepath = self.processed_path / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'wb') as f:
                f.write(data)

            logger.info(f"Processed file saved: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save processed file: {e}")
            return False

    def get_processed(self, filename: str) -> Optional[bytes]:
        """Get processed file."""
        try:
            filepath = self.processed_path / filename
            if not filepath.exists():
                logger.warning(f"Processed file not found: {filepath}")
                return None

            with open(filepath, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to get processed file: {e}")
            return None

    def archive(self, filename: str) -> bool:
        """Move file to archive."""
        try:
            # Try temp path
            src = self.base_path / filename
            if not src.exists():
                # Try processed path
                src = self.processed_path / filename

            if not src.exists():
                logger.warning(f"File not found for archiving: {filename}")
                return False

            dst = self.archive_path / filename
            shutil.move(str(src), str(dst))

            logger.info(f"File archived: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to archive file: {e}")
            return False

    def delete(self, filename: str) -> bool:
        """Delete file."""
        try:
            # Try all paths
            paths = [
                self.base_path / filename,
                self.processed_path / filename,
                self.archive_path / filename
            ]

            for path in paths:
                if path.exists():
                    path.unlink()
                    logger.info(f"File deleted: {path}")
                    return True

            logger.warning(f"File not found for deletion: {filename}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def list_files(self, path: Optional[str] = None) -> list:
        """List files in storage."""
        try:
            base = Path(path) if path else self.base_path
            if not base.exists():
                return []

            return [f.name for f in base.iterdir() if f.is_file()]
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def get_file_size(self, filename: str) -> int:
        """Get file size."""
        try:
            paths = [
                self.base_path / filename,
                self.processed_path / filename,
                self.archive_path / filename
            ]

            for path in paths:
                if path.exists():
                    return path.stat().st_size

            return 0
        except Exception as e:
            logger.error(f"Failed to get file size: {e}")
            return 0