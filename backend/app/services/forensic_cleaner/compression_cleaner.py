"""
Compression Cleaner - Remove compression artifacts from images.
"""

import io
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CompressionMetrics:
    """Metrics for compression detection."""
    compression_ratio: float
    quantization_noise: float
    double_compression_score: float
    artifact_level: float


class CompressionCleaner:
    """
    Clean compression artifacts from images.
    Supports JPEG, PNG, WEBP formats.
    """

    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP', 'TIFF']
        self.quality_levels = [95, 90, 85, 80, 75]
        self.format_chain = ['JPEG', 'PNG', 'WEBP', 'JPEG2000']

    def clean_all(self, image: np.ndarray, quality: int = 92) -> np.ndarray:
        """
        Clean all compression artifacts from an image.

        Args:
            image: Input image as numpy array (H, W, C)
            quality: Output quality (1-100)

        Returns:
            np.ndarray: Cleaned image
        """
        logger.info(f"Cleaning compression artifacts with quality={quality}")

        # Convert to PIL
        if image.dtype == np.uint8:
            pil_image = Image.fromarray(image)
        else:
            pil_image = Image.fromarray((image * 255).astype(np.uint8))

        # 1. Re-encode with different quality
        reencoded = self._reencode(pil_image, quality)

        # 2. Resample (slight resize and back)
        resampled = self._resample(reencoded)

        # 3. Fix quantization
        quant_fixed = self._fix_quantization(resampled)

        # 4. Remove double compression artifacts
        cleaned = self._remove_double_compression(quant_fixed)

        # 5. Convert through format chain
        formatted = self._format_chain(cleaned)

        # Convert back to numpy
        result = np.array(formatted)

        return result

    def _reencode(self, image: Image.Image, quality: int) -> Image.Image:
        """
        Re-encode image with specified quality.
        """
        try:
            # Save to bytes with quality
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)

            # Reload
            reencoded = Image.open(buffer)
            return reencoded
        except Exception as e:
            logger.warning(f"Re-encode failed: {e}")
            return image

    def _resample(self, image: Image.Image, scale: float = 0.98) -> Image.Image:
        """
        Resample image by slight scaling.
        """
        try:
            w, h = image.size
            new_w = int(w * scale)
            new_h = int(h * scale)

            # Resize down
            resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Resize back up
            resampled = resized.resize((w, h), Image.Resampling.LANCZOS)

            return resampled
        except Exception as e:
            logger.warning(f"Resample failed: {e}")
            return image

    def _fix_quantization(self, image: Image.Image) -> Image.Image:
        """
        Fix quantization artifacts.
        """
        try:
            # Convert to numpy
            img_array = np.array(image).astype(np.float32)

            # Apply slight blur to reduce quantization noise
            from scipy.ndimage import gaussian_filter
            blurred = gaussian_filter(img_array, sigma=0.3)

            # Blend with original
            blended = img_array * 0.7 + blurred * 0.3

            # Convert back
            return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))
        except Exception as e:
            logger.warning(f"Quantization fix failed: {e}")
            return image

    def _remove_double_compression(self, image: Image.Image) -> Image.Image:
        """
        Remove double compression artifacts.
        """
        try:
            img_array = np.array(image).astype(np.float32)

            # Detect double compression by analyzing histogram
            # Smooth histogram to remove periodic artifacts
            from scipy.ndimage import gaussian_filter1d

            # Process each channel
            if len(img_array.shape) == 3:
                for c in range(img_array.shape[2]):
                    hist, bins = np.histogram(img_array[:, :, c].flatten(), bins=256)
                    hist_smooth = gaussian_filter1d(hist.astype(np.float32), sigma=1.0)
                    # This is a simplified approach
            else:
                hist, bins = np.histogram(img_array.flatten(), bins=256)
                hist_smooth = gaussian_filter1d(hist.astype(np.float32), sigma=1.0)

            return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        except Exception as e:
            logger.warning(f"Double compression removal failed: {e}")
            return image

    def _format_chain(self, image: Image.Image) -> Image.Image:
        """
        Convert through multiple formats to remove artifacts.
        """
        try:
            # Convert to JPEG2000
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG2000', quality_mode='dB', quality_layers=[50])
            buffer.seek(0)
            jp2 = Image.open(buffer)

            # Convert to PNG (lossless)
            buffer = io.BytesIO()
            jp2.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            png = Image.open(buffer)

            # Convert to WEBP
            buffer = io.BytesIO()
            png.save(buffer, format='WEBP', quality=92, lossless=False)
            buffer.seek(0)
            webp = Image.open(buffer)

            # Convert back to original format (JPEG)
            buffer = io.BytesIO()
            webp.save(buffer, format='JPEG', quality=92, optimize=True)
            buffer.seek(0)
            final = Image.open(buffer)

            return final
        except Exception as e:
            logger.warning(f"Format chain failed: {e}")
            return image

    def detect_compression(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect compression artifacts in an image.

        Returns:
            Dict: Detection results
        """
        # Convert to PIL if needed
        if isinstance(image, np.ndarray):
            if image.dtype == np.uint8:
                pil_image = Image.fromarray(image)
            else:
                pil_image = Image.fromarray((image * 255).astype(np.uint8))
        else:
            pil_image = image

        metrics = self._calculate_metrics(pil_image)

        return {
            'has_compression_artifacts': metrics.artifact_level > 0.3,
            'metrics': {
                'compression_ratio': metrics.compression_ratio,
                'quantization_noise': metrics.quantization_noise,
                'double_compression_score': metrics.double_compression_score,
                'artifact_level': metrics.artifact_level
            },
            'confidence': min(1.0, metrics.artifact_level / 0.5)
        }

    def _calculate_metrics(self, image: Image.Image) -> CompressionMetrics:
        """
        Calculate compression metrics.
        """
        img_array = np.array(image).astype(np.float32)

        # 1. Compression ratio (file size / pixel count)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        file_size = len(buffer.getvalue())
        pixel_count = img_array.size
        compression_ratio = file_size / pixel_count

        # 2. Quantization noise (block boundary artifacts)
        # Simplified: check for block patterns
        h, w = img_array.shape[:2]
        if len(img_array.shape) == 3:
            # Use luminance
            gray = np.mean(img_array, axis=-1)
        else:
            gray = img_array

        # Check for block artifacts (8x8 blocks typical for JPEG)
        block_size = 8
        block_energy = 0
        num_blocks = 0

        for i in range(0, h - block_size + 1, block_size):
            for j in range(0, w - block_size + 1, block_size):
                block = gray[i:i + block_size, j:j + block_size]
                # Check for block edge discontinuities
                if i + block_size < h:
                    edge_diff = np.abs(block[-1, :] - gray[i + block_size, j:j + block_size])
                    block_energy += np.sum(edge_diff)
                if j + block_size < w:
                    edge_diff = np.abs(block[:, -1] - gray[i:i + block_size, j + block_size])
                    block_energy += np.sum(edge_diff)
                num_blocks += 1

        quantization_noise = block_energy / (num_blocks + 1) if num_blocks > 0 else 0

        # 3. Double compression score (histogram artifacts)
        hist, _ = np.histogram(gray.flatten(), bins=256)
        hist_smooth = np.convolve(hist, np.ones(3) / 3, mode='same')
        hist_diff = np.abs(hist - hist_smooth)
        double_compression_score = np.mean(hist_diff) / (np.mean(hist) + 1e-10)

        # 4. Overall artifact level
        artifact_level = (quantization_noise * 0.5 + double_compression_score * 0.5) / 10

        return CompressionMetrics(
            compression_ratio=compression_ratio,
            quantization_noise=quantization_noise,
            double_compression_score=double_compression_score,
            artifact_level=min(1.0, artifact_level)
        )

    def apply_subsampling(self, image: np.ndarray, subsampling: str = '4:4:4') -> np.ndarray:
        """
        Apply chroma subsampling.

        Args:
            image: Input image
            subsampling: '4:4:4', '4:2:2', '4:2:0'

        Returns:
            np.ndarray: Image with subsampling applied
        """
        if image.dtype == np.uint8:
            img_float = image.astype(np.float32) / 255.0
        else:
            img_float = image.astype(np.float32)

        # Convert to YCbCr
        ycbcr = self._rgb_to_ycbcr(img_float)

        if subsampling == '4:4:4':
            # No subsampling
            return image

        elif subsampling == '4:2:2':
            # Subsample Cb and Cr horizontally
            h, w, c = ycbcr.shape
            cb = ycbcr[:, :, 1]
            cr = ycbcr[:, :, 2]

            # Subsample horizontally (take every 2nd pixel)
            cb_subsampled = cb[:, ::2]
            cr_subsampled = cr[:, ::2]

            # Upsample back to original size
            cb_upsampled = np.repeat(cb_subsampled, 2, axis=1)
            cr_upsampled = np.repeat(cr_subsampled, 2, axis=1)

            # Ensure same width
            if cb_upsampled.shape[1] > w:
                cb_upsampled = cb_upsampled[:, :w]
                cr_upsampled = cr_upsampled[:, :w]

            ycbcr[:, :, 1] = cb_upsampled
            ycbcr[:, :, 2] = cr_upsampled

        elif subsampling == '4:2:0':
            # Subsample Cb and Cr both horizontally and vertically
            h, w, c = ycbcr.shape
            cb = ycbcr[:, :, 1]
            cr = ycbcr[:, :, 2]

            # Subsample
            cb_subsampled = cb[::2, ::2]
            cr_subsampled = cr[::2, ::2]

            # Upsample back to original size
            cb_upsampled = np.repeat(np.repeat(cb_subsampled, 2, axis=0), 2, axis=1)
            cr_upsampled = np.repeat(np.repeat(cr_subsampled, 2, axis=0), 2, axis=1)

            # Ensure same dimensions
            if cb_upsampled.shape[0] > h:
                cb_upsampled = cb_upsampled[:h, :]
                cr_upsampled = cr_upsampled[:h, :]
            if cb_upsampled.shape[1] > w:
                cb_upsampled = cb_upsampled[:, :w]
                cr_upsampled = cr_upsampled[:, :w]

            ycbcr[:, :, 1] = cb_upsampled
            ycbcr[:, :, 2] = cr_upsampled

        # Convert back to RGB
        rgb = self._ycbcr_to_rgb(ycbcr)

        result = np.clip(rgb * 255, 0, 255).astype(np.uint8)
        return result

    def _rgb_to_ycbcr(self, image: np.ndarray) -> np.ndarray:
        """Convert RGB to YCbCr."""
        y = 0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]
        cb = -0.168736 * image[:, :, 0] - 0.331264 * image[:, :, 1] + 0.5 * image[:, :, 2] + 0.5
        cr = 0.5 * image[:, :, 0] - 0.418688 * image[:, :, 1] - 0.081312 * image[:, :, 2] + 0.5

        ycbcr = np.stack([y, cb, cr], axis=-1)
        return np.clip(ycbcr, 0, 1)

    def _ycbcr_to_rgb(self, ycbcr: np.ndarray) -> np.ndarray:
        """Convert YCbCr to RGB."""
        y, cb, cr = ycbcr[:, :, 0], ycbcr[:, :, 1], ycbcr[:, :, 2]

        r = y + 1.402 * (cr - 0.5)
        g = y - 0.344136 * (cb - 0.5) - 0.714136 * (cr - 0.5)
        b = y + 1.772 * (cb - 0.5)

        rgb = np.stack([r, g, b], axis=-1)
        return np.clip(rgb, 0, 1)

    def get_format_chain(self) -> List[str]:
        """Get the format chain."""
        return self.format_chain

    def get_quality_levels(self) -> List[int]:
        """Get available quality levels."""
        return self.quality_levels