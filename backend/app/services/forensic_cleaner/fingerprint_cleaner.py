"""
Fingerprint Cleaner - Remove GAN, Diffusion, and AI model fingerprints from images.
"""

import numpy as np
from scipy import stats
from scipy.ndimage import gaussian_filter
import logging
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FingerprintMetrics:
    """Metrics for fingerprint detection."""
    cross_channel_correlation: float
    entropy: float
    spectral_features: List[float]
    pca_components: List[float]
    anomaly_score: float


class FingerprintCleaner:
    """
    Remove AI model fingerprints from images.
    Supports GAN, Diffusion, and other generative model fingerprints.
    """

    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'TIFF', 'WEBP']

    def clean_all(self, image: np.ndarray) -> np.ndarray:
        """
        Clean all fingerprints from an image.

        Args:
            image: Input image as numpy array (H, W, C)

        Returns:
            np.ndarray: Image with fingerprints removed
        """
        logger.info("Cleaning fingerprints...")

        # Convert to float
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        # 1. Apply YCbCr transformation
        ycbcr = self._rgb_to_ycbcr(image_float)

        # 2. Clean each channel
        ycbcr_cleaned = self._clean_ycbcr(ycbcr)

        # 3. Convert back to RGB
        cleaned = self._ycbcr_to_rgb(ycbcr_cleaned)

        # 4. Remove cross-channel correlations
        cleaned = self._remove_cross_channel_correlation(cleaned)

        # 5. Apply SVD-based fingerprint removal
        cleaned = self._remove_svd_fingerprint(cleaned)

        # Convert back to uint8
        result = np.clip(cleaned * 255, 0, 255).astype(np.uint8)

        return result

    def _rgb_to_ycbcr(self, image: np.ndarray) -> np.ndarray:
        """
        Convert RGB to YCbCr color space.

        Y  =  0.299 * R + 0.587 * G + 0.114 * B
        Cb = -0.168736 * R - 0.331264 * G + 0.5 * B + 0.5
        Cr =  0.5 * R - 0.418688 * G - 0.081312 * B + 0.5
        """
        y = 0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]
        cb = -0.168736 * image[:, :, 0] - 0.331264 * image[:, :, 1] + 0.5 * image[:, :, 2] + 0.5
        cr = 0.5 * image[:, :, 0] - 0.418688 * image[:, :, 1] - 0.081312 * image[:, :, 2] + 0.5

        ycbcr = np.stack([y, cb, cr], axis=-1)
        return np.clip(ycbcr, 0, 1)

    def _ycbcr_to_rgb(self, ycbcr: np.ndarray) -> np.ndarray:
        """
        Convert YCbCr to RGB color space.
        """
        y, cb, cr = ycbcr[:, :, 0], ycbcr[:, :, 1], ycbcr[:, :, 2]

        r = y + 1.402 * (cr - 0.5)
        g = y - 0.344136 * (cb - 0.5) - 0.714136 * (cr - 0.5)
        b = y + 1.772 * (cb - 0.5)

        rgb = np.stack([r, g, b], axis=-1)
        return np.clip(rgb, 0, 1)

    def _clean_ycbcr(self, ycbcr: np.ndarray) -> np.ndarray:
        """
        Clean YCbCr channels by adding noise and smoothing.
        """
        cleaned = ycbcr.copy()

        # Clean Y channel (luminance) - keep detail
        y_noise = np.random.randn(*ycbcr[:, :, 0].shape) * 0.001
        cleaned[:, :, 0] += y_noise

        # Clean Cb channel - more aggressive
        cb_noise = np.random.randn(*ycbcr[:, :, 1].shape) * 0.005
        cleaned[:, :, 1] += cb_noise
        cleaned[:, :, 1] = gaussian_filter(cleaned[:, :, 1], sigma=0.5)

        # Clean Cr channel - more aggressive
        cr_noise = np.random.randn(*ycbcr[:, :, 2].shape) * 0.005
        cleaned[:, :, 2] += cr_noise
        cleaned[:, :, 2] = gaussian_filter(cleaned[:, :, 2], sigma=0.5)

        return np.clip(cleaned, 0, 1)

    def _remove_cross_channel_correlation(self, image: np.ndarray) -> np.ndarray:
        """
        Remove cross-channel correlations (common in GANs).
        """
        h, w, c = image.shape

        # Add small noise to break correlations
        noise = np.random.randn(h, w, c) * 0.002
        image_noisy = image + noise

        # Clamp
        return np.clip(image_noisy, 0, 1)

    def _remove_svd_fingerprint(self, image: np.ndarray) -> np.ndarray:
        """
        Remove SVD-based fingerprints.
        """
        h, w, c = image.shape

        # Use SVD instead of PCA (no sklearn dependency)
        if len(image.shape) == 3:
            for channel in range(c):
                # Apply SVD to each channel
                U, s, Vt = np.linalg.svd(image[:, :, channel], full_matrices=False)

                # Keep only top components (remove fingerprint)
                n_components = min(32, len(s))
                s_reduced = s.copy()
                if n_components < len(s):
                    s_reduced[n_components:] = 0

                # Reconstruct
                reconstructed = U @ np.diag(s_reduced) @ Vt

                # Blend with original
                image[:, :, channel] = image[:, :, channel] * 0.7 + reconstructed * 0.3
        else:
            # Grayscale image
            U, s, Vt = np.linalg.svd(image, full_matrices=False)
            n_components = min(32, len(s))
            s_reduced = s.copy()
            if n_components < len(s):
                s_reduced[n_components:] = 0
            reconstructed = U @ np.diag(s_reduced) @ Vt
            image = image * 0.7 + reconstructed * 0.3

        return np.clip(image, 0, 1)

    def detect_fingerprint(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect AI fingerprints in an image.

        Returns:
            Dict: Detection results
        """
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        metrics = self._calculate_metrics(image_float)

        return {
            'has_fingerprint': metrics.anomaly_score > 0.3,
            'metrics': {
                'cross_channel_correlation': metrics.cross_channel_correlation,
                'entropy': metrics.entropy,
                'pca_components': metrics.pca_components[:5],
                'anomaly_score': metrics.anomaly_score
            },
            'confidence': min(1.0, metrics.anomaly_score / 0.5)
        }

    def _calculate_metrics(self, image: np.ndarray) -> FingerprintMetrics:
        """Calculate fingerprint metrics."""
        h, w, c = image.shape

        # 1. Cross-channel correlation
        channels_flat = image.reshape(-1, c)
        corr_matrix = np.corrcoef(channels_flat.T)
        cross_corr = np.mean(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])

        # 2. Entropy
        entropy = self._calculate_entropy(image)

        # 3. Spectral features
        spectral_features = self._calculate_spectral_features(image)

        # 4. SVD components
        patches = self._extract_patches(image, patch_size=8)
        if patches.shape[0] > 10:
            # Use SVD
            U, s, Vt = np.linalg.svd(patches, full_matrices=False)
            pca_components = (s / np.sum(s)).tolist()[:16]
        else:
            pca_components = []

        # 5. Anomaly score
        anomaly_score = self._calculate_anomaly_score(image, cross_corr, entropy)

        return FingerprintMetrics(
            cross_channel_correlation=cross_corr,
            entropy=entropy,
            spectral_features=spectral_features,
            pca_components=pca_components,
            anomaly_score=anomaly_score
        )

    def _calculate_entropy(self, image: np.ndarray) -> float:
        """Calculate image entropy."""
        # Flatten and discretize
        flat = image.flatten()
        hist, _ = np.histogram(flat, bins=64, range=(0, 1))

        # Normalize
        hist = hist / (hist.sum() + 1e-10)

        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))

        return entropy

    def _calculate_spectral_features(self, image: np.ndarray) -> List[float]:
        """Calculate spectral features using FFT."""
        if len(image.shape) == 3:
            # Average across channels
            image_gray = np.mean(image, axis=-1)
        else:
            image_gray = image

        # FFT
        fft = np.fft.fft2(image_gray)
        magnitude = np.abs(np.fft.fftshift(fft))

        # Features
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Low frequency energy
        low_freq = magnitude[center_h - 10:center_h + 10, center_w - 10:center_w + 10]
        low_energy = np.sum(low_freq)

        # High frequency energy
        high_freq = magnitude.copy()
        high_freq[center_h - 20:center_h + 20, center_w - 20:center_w + 20] = 0
        high_energy = np.sum(high_freq)

        # Ratio
        ratio = high_energy / (low_energy + 1e-10)

        return [float(low_energy), float(high_energy), float(ratio)]

    def _calculate_anomaly_score(self, image: np.ndarray, cross_corr: float,
                                 entropy: float) -> float:
        """Calculate anomaly score based on metrics."""
        score = 0.0

        # High cross-channel correlation is suspicious (GANs have high correlation)
        score += min(1.0, cross_corr * 2)

        # Low entropy is suspicious (GANs produce less varied images)
        if entropy < 3.0:
            score += 0.3
        elif entropy > 7.0:
            score -= 0.2

        return np.clip(score, 0, 1)

    def remove_gan_fingerprint(self, image: np.ndarray) -> np.ndarray:
        """
        Specifically target GAN fingerprints.
        """
        # 1. Apply frequency domain filtering
        fft = np.fft.fft2(image.mean(axis=-1) if len(image.shape) == 3 else image)
        fft_shifted = np.fft.fftshift(fft)

        # Suppress high-frequency peaks (GAN artifacts)
        h, w = fft_shifted.shape
        center_h, center_w = h // 2, w // 2

        # Create Gaussian notch filter
        sigma = 10
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_w) ** 2 + (y - center_h) ** 2)
        gaussian = 1 - np.exp(-(distance ** 2) / (2 * sigma ** 2))

        # Apply to all channels
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                channel_fft = np.fft.fft2(image[:, :, c])
                channel_fft_shifted = np.fft.fftshift(channel_fft)
                channel_fft_shifted *= gaussian
                channel_cleaned = np.fft.ifft2(np.fft.ifftshift(channel_fft_shifted))
                image[:, :, c] = np.real(channel_cleaned)
        else:
            fft_shifted *= gaussian
            image = np.real(np.fft.ifft2(np.fft.ifftshift(fft_shifted)))

        return np.clip(image, 0, 1)

    def remove_diffusion_fingerprint(self, image: np.ndarray) -> np.ndarray:
        """
        Specifically target Diffusion model fingerprints.
        """
        # 1. Apply adaptive smoothing
        smoothed = gaussian_filter(image, sigma=0.3)

        # 2. Blend with original
        result = image * 0.6 + smoothed * 0.4

        # 3. Add controlled noise to break latent patterns
        noise = np.random.randn(*image.shape) * 0.005
        result += noise

        return np.clip(result, 0, 1)

    def _extract_patches(self, image: np.ndarray, patch_size: int = 8) -> np.ndarray:
        """Extract patches from image."""
        h, w, c = image.shape
        patches = []

        for i in range(0, h - patch_size + 1, patch_size // 2):
            for j in range(0, w - patch_size + 1, patch_size // 2):
                patch = image[i:i + patch_size, j:j + patch_size].reshape(-1)
                patches.append(patch)

        return np.array(patches)

    def _reconstruct_patches(self, patches: np.ndarray, shape: Tuple[int, int, int],
                            patch_size: int = 8) -> np.ndarray:
        """Reconstruct image from patches."""
        h, w, c = shape
        result = np.zeros((h, w, c), dtype=np.float32)
        counts = np.zeros((h, w), dtype=np.float32)

        idx = 0
        for i in range(0, h - patch_size + 1, patch_size // 2):
            for j in range(0, w - patch_size + 1, patch_size // 2):
                patch = patches[idx].reshape(patch_size, patch_size, c)
                result[i:i + patch_size, j:j + patch_size] += patch
                counts[i:i + patch_size, j:j + patch_size] += 1
                idx += 1

        # Average overlapping patches
        counts = np.maximum(counts, 1)
        result /= counts[..., None]

        return result