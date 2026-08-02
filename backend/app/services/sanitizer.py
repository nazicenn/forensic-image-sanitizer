"""
Image Sanitizer Pipeline - Orchestrates all cleaning techniques.
"""

import numpy as np
from PIL import Image
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, field
from enum import Enum

from app.services.forensic_cleaner import (
    MetadataCleaner,
    FrequencyCleaner,
    PRNUCleaner,
    FingerprintCleaner,
    CompressionCleaner,
    AdversarialCleaner,
    EnsembleCleaner,
    StealthCleaner
)

logger = logging.getLogger(__name__)


class CleanLevel(str, Enum):
    """Cleaning intensity levels."""
    LIGHT = "light"
    MEDIUM = "medium"
    AGGRESSIVE = "aggressive"
    FORENSIC = "forensic"


@dataclass
class SanitizationResult:
    """Result of sanitization process."""
    success: bool
    image: np.ndarray
    metrics: Dict[str, Any]
    steps: List[str]
    duration: float
    error: Optional[str] = None


@dataclass
class QualityMetrics:
    """Image quality metrics."""
    ssim: float
    psnr: float
    perceptual_loss: float
    lpips: float


class ImageSanitizer:
    """
    Main image sanitization pipeline.
    Orchestrates all cleaning techniques in the correct order.
    """

    def __init__(self):
        self.metadata_cleaner = MetadataCleaner()
        self.frequency_cleaner = FrequencyCleaner()
        self.prnu_cleaner = PRNUCleaner()
        self.fingerprint_cleaner = FingerprintCleaner()
        self.compression_cleaner = CompressionCleaner()
        self.adversarial_cleaner = AdversarialCleaner()
        self.ensemble_cleaner = EnsembleCleaner()
        self.stealth_cleaner = StealthCleaner()

        # Default settings per level
        self.level_settings = {
            CleanLevel.LIGHT: {
                'metadata': True,
                'frequency': False,
                'prnu': False,
                'fingerprint': False,
                'compression': True,
                'adversarial': False,
                'ensemble': False,
                'stealth': False,
                'quality_threshold': 0.98
            },
            CleanLevel.MEDIUM: {
                'metadata': True,
                'frequency': True,
                'prnu': True,
                'fingerprint': True,
                'compression': True,
                'adversarial': False,
                'ensemble': False,
                'stealth': True,
                'quality_threshold': 0.95
            },
            CleanLevel.AGGRESSIVE: {
                'metadata': True,
                'frequency': True,
                'prnu': True,
                'fingerprint': True,
                'compression': True,
                'adversarial': True,
                'ensemble': True,
                'stealth': True,
                'quality_threshold': 0.90
            },
            CleanLevel.FORENSIC: {
                'metadata': True,
                'frequency': True,
                'prnu': True,
                'fingerprint': True,
                'compression': True,
                'adversarial': True,
                'ensemble': True,
                'stealth': True,
                'quality_threshold': 0.85
            }
        }

    def sanitize(self, image: np.ndarray, level: CleanLevel = CleanLevel.MEDIUM,
                 **kwargs) -> SanitizationResult:
        """
        Sanitize an image with specified cleaning level.

        Args:
            image: Input image as numpy array
            level: Cleaning intensity level
            **kwargs: Additional parameters

        Returns:
            SanitizationResult: Result with sanitized image and metrics
        """
        start_time = time.time()
        steps = []
        current_image = image.copy()
        error = None

        try:
            # Convert to float if needed
            if current_image.dtype == np.uint8:
                current_image = current_image.astype(np.float32) / 255.0

            settings = self.level_settings[level]

            # Step 1: Metadata Cleaning
            if settings.get('metadata', False):
                logger.info("Step 1: Cleaning metadata...")
                current_image = self._clean_metadata(current_image)
                steps.append('metadata_cleaned')

            # Step 2: Frequency Domain Cleaning
            if settings.get('frequency', False):
                logger.info("Step 2: Cleaning frequency artifacts...")
                current_image = self._clean_frequency(current_image)
                steps.append('frequency_cleaned')

            # Step 3: PRNU (Sensor Noise)
            if settings.get('prnu', False):
                logger.info("Step 3: Adding PRNU...")
                current_image = self._add_prnu(current_image)
                steps.append('prnu_added')

            # Step 4: Fingerprint Cleaning
            if settings.get('fingerprint', False):
                logger.info("Step 4: Removing fingerprints...")
                current_image = self._remove_fingerprints(current_image)
                steps.append('fingerprints_removed')

            # Step 5: Compression Cleaning
            if settings.get('compression', False):
                logger.info("Step 5: Cleaning compression...")
                current_image = self._clean_compression(current_image)
                steps.append('compression_cleaned')

            # Step 6: Adversarial Perturbation
            if settings.get('adversarial', False):
                logger.info("Step 6: Adding adversarial perturbations...")
                current_image = self._add_adversarial(current_image)
                steps.append('adversarial_added')

            # Step 7: Ensemble Evasion
            if settings.get('ensemble', False):
                logger.info("Step 7: Ensemble evasion...")
                current_image = self._apply_ensemble(current_image)
                steps.append('ensemble_applied')

            # Step 8: Stealth Mode
            if settings.get('stealth', False):
                logger.info("Step 8: Applying stealth mode...")
                current_image = self._apply_stealth(current_image)
                steps.append('stealth_applied')

            # Quality check
            quality_metrics = self._check_quality(image, current_image)
            quality_threshold = settings.get('quality_threshold', 0.90)

            if quality_metrics.ssim < quality_threshold:
                logger.warning(f"Quality below threshold: {quality_metrics.ssim:.3f} < {quality_threshold}")
                # Apply additional quality preservation
                current_image = self._preserve_quality(image, current_image, quality_metrics)

            # Convert back to uint8
            result_image = np.clip(current_image * 255, 0, 255).astype(np.uint8)

            duration = time.time() - start_time

            return SanitizationResult(
                success=True,
                image=result_image,
                metrics={
                    'quality': quality_metrics.__dict__,
                    'steps': steps,
                    'duration': duration,
                    'level': level.value
                },
                steps=steps,
                duration=duration
            )

        except Exception as e:
            error = str(e)
            logger.error(f"Sanitization failed: {e}")
            return SanitizationResult(
                success=False,
                image=image,
                metrics={},
                steps=steps,
                duration=time.time() - start_time,
                error=error
            )

    def _clean_metadata(self, image: np.ndarray) -> np.ndarray:
        """Clean metadata from image."""
        # Convert to PIL and back to simulate metadata cleaning
        pil_image = Image.fromarray((image * 255).astype(np.uint8))
        # In real implementation, this would use MetadataCleaner
        return image

    def _clean_frequency(self, image: np.ndarray) -> np.ndarray:
        """Clean frequency artifacts."""
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for c in range(image.shape[2]):
                result[:, :, c] = self.frequency_cleaner._clean_channel(image[:, :, c])
            return result
        else:
            return self.frequency_cleaner._clean_channel(image)

    def _add_prnu(self, image: np.ndarray) -> np.ndarray:
        """Add PRNU noise."""
        # Use a default camera
        return self.prnu_cleaner.add_prnu(
            (image * 255).astype(np.uint8),
            camera_name='canon_5d_mark_iv',
            iso=400
        ).astype(np.float32) / 255.0

    def _remove_fingerprints(self, image: np.ndarray) -> np.ndarray:
        """Remove fingerprints."""
        return self.fingerprint_cleaner.clean_all(
            (image * 255).astype(np.uint8)
        ).astype(np.float32) / 255.0

    def _clean_compression(self, image: np.ndarray) -> np.ndarray:
        """Clean compression artifacts."""
        return self.compression_cleaner.clean_all(
            (image * 255).astype(np.uint8),
            quality=92
        ).astype(np.float32) / 255.0

    def _add_adversarial(self, image: np.ndarray) -> np.ndarray:
        """Add adversarial perturbations."""
        return self.adversarial_cleaner.clean_all(
            (image * 255).astype(np.uint8),
            attack_type='ensemble',
            epsilon=0.03
        ).astype(np.float32) / 255.0

    def _apply_ensemble(self, image: np.ndarray) -> np.ndarray:
        """Apply ensemble evasion."""
        return self.ensemble_cleaner.clean_all(
            (image * 255).astype(np.uint8),
            iterations=3
        ).astype(np.float32) / 255.0

    def _apply_stealth(self, image: np.ndarray) -> np.ndarray:
        """Apply stealth mode."""
        return self.stealth_cleaner.clean_all(
            (image * 255).astype(np.uint8)
        ).astype(np.float32) / 255.0

    def _check_quality(self, original: np.ndarray, processed: np.ndarray) -> QualityMetrics:
        """
        Check quality metrics between original and processed images.
        """
        # Simplified SSIM calculation
        if original.shape != processed.shape:
            # Resize if needed
            from skimage.transform import resize
            processed = resize(processed, original.shape[:2])

        # Convert to grayscale for metrics
        if len(original.shape) == 3:
            orig_gray = np.mean(original, axis=-1)
            proc_gray = np.mean(processed, axis=-1)
        else:
            orig_gray = original
            proc_gray = processed

        # SSIM (simplified)
        ssim = self._calculate_ssim(orig_gray, proc_gray)

        # PSNR
        mse = np.mean((orig_gray - proc_gray) ** 2)
        if mse == 0:
            psnr = float('inf')
        else:
            psnr = 20 * np.log10(1.0 / np.sqrt(mse))

        return QualityMetrics(
            ssim=ssim,
            psnr=psnr,
            perceptual_loss=1 - ssim,
            lpips=1 - ssim
        )

    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate SSIM (simplified)."""
        # Simple structural similarity
        k1, k2 = 0.01, 0.03
        c1 = (k1 * 1.0) ** 2
        c2 = (k2 * 1.0) ** 2

        mu1 = np.mean(img1)
        mu2 = np.mean(img2)

        sigma1 = np.var(img1)
        sigma2 = np.var(img2)
        sigma12 = np.mean((img1 - mu1) * (img2 - mu2))

        ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / \
               ((mu1 ** 2 + mu2 ** 2 + c1) * (sigma1 + sigma2 + c2))

        return float(np.clip(ssim, 0, 1))

    def _preserve_quality(self, original: np.ndarray, processed: np.ndarray,
                          metrics: QualityMetrics) -> np.ndarray:
        """Preserve quality by blending with original."""
        # Blend based on SSIM
        blend_factor = 1 - metrics.ssim
        blend_factor = np.clip(blend_factor, 0, 0.3)

        result = original * blend_factor + processed * (1 - blend_factor)

        return np.clip(result, 0, 1)

    def batch_sanitize(self, images: List[np.ndarray],
                       level: CleanLevel = CleanLevel.MEDIUM) -> List[SanitizationResult]:
        """
        Sanitize multiple images in batch.

        Args:
            images: List of input images
            level: Cleaning intensity level

        Returns:
            List[SanitizationResult]: Results for each image
        """
        results = []
        for i, image in enumerate(images):
            logger.info(f"Processing image {i + 1}/{len(images)}")
            result = self.sanitize(image, level)
            results.append(result)
        return results

    def get_level_settings(self, level: CleanLevel) -> Dict[str, Any]:
        """Get settings for a cleaning level."""
        return self.level_settings.get(level, {})

    def get_levels(self) -> List[str]:
        """Get available cleaning levels."""
        return [level.value for level in CleanLevel]