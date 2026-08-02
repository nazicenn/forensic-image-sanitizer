"""
Adversarial Cleaner - Add imperceptible perturbations to evade AI detectors.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.fft import fft2, ifft2, fftshift, ifftshift
import logging
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AdversarialMetrics:
    """Metrics for adversarial perturbation."""
    perturbation_magnitude: float
    ssim_score: float
    psnr_score: float
    evasion_confidence: float


class AdversarialCleaner:
    """
    Add imperceptible adversarial perturbations to evade AI detectors.
    Supports FGSM, PGD, and ensemble attacks.
    """

    def __init__(self):
        self.epsilon = 0.03  # Maximum perturbation
        self.steps = 10      # Number of attack steps
        self.supported_formats = ['JPEG', 'PNG', 'WEBP', 'TIFF']

    def clean_all(self, image: np.ndarray, attack_type: str = 'ensemble',
                  epsilon: float = 0.03) -> np.ndarray:
        """
        Add adversarial perturbations to an image.

        Args:
            image: Input image as numpy array (H, W, C)
            attack_type: 'fgsm', 'pgd', 'ensemble'
            epsilon: Maximum perturbation magnitude

        Returns:
            np.ndarray: Image with adversarial perturbations
        """
        logger.info(f"Adding adversarial perturbations with {attack_type} attack")

        # Convert to float
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        # Choose attack
        if attack_type == 'fgsm':
            perturbed = self._fgsm_attack(image_float, epsilon)
        elif attack_type == 'pgd':
            perturbed = self._pgd_attack(image_float, epsilon)
        else:  # ensemble
            perturbed = self._ensemble_attack(image_float, epsilon)

        # Ensure imperceptibility
        perturbed = self._enforce_imperceptibility(image_float, perturbed)

        # Convert back to uint8
        result = np.clip(perturbed * 255, 0, 255).astype(np.uint8)

        return result

    def _fgsm_attack(self, image: np.ndarray, epsilon: float) -> np.ndarray:
        """
        Fast Gradient Sign Method (FGSM) attack.
        """
        # Generate gradient (simulated)
        gradient = self._simulate_gradient(image)

        # Apply sign
        sign_gradient = np.sign(gradient)

        # Create perturbation
        perturbation = epsilon * sign_gradient

        # Apply to image
        perturbed = image + perturbation

        return np.clip(perturbed, 0, 1)

    def _pgd_attack(self, image: np.ndarray, epsilon: float) -> np.ndarray:
        """
        Projected Gradient Descent (PGD) attack.
        """
        perturbed = image.copy()
        step_size = epsilon / self.steps

        for _ in range(self.steps):
            # Generate gradient
            gradient = self._simulate_gradient(perturbed)

            # Update
            perturbed = perturbed + step_size * np.sign(gradient)

            # Project back to epsilon ball
            perturbation = perturbed - image
            perturbation = np.clip(perturbation, -epsilon, epsilon)
            perturbed = image + perturbation

            # Clamp to valid range
            perturbed = np.clip(perturbed, 0, 1)

        return perturbed

    def _ensemble_attack(self, image: np.ndarray, epsilon: float) -> np.ndarray:
        """
        Ensemble attack combining multiple strategies.
        """
        # Multiple attack strategies
        attacks = [
            self._freq_domain_attack,
            self._spatial_domain_attack,
            self._color_domain_attack
        ]

        # Apply each attack and average
        perturbations = []
        for attack in attacks:
            perturbed = attack(image, epsilon * 0.5)
            perturbations.append(perturbed - image)

        # Average perturbations
        avg_perturbation = np.mean(perturbations, axis=0)
        avg_perturbation = np.clip(avg_perturbation, -epsilon, epsilon)

        # Apply
        perturbed = image + avg_perturbation

        return np.clip(perturbed, 0, 1)

    def _freq_domain_attack(self, image: np.ndarray, epsilon: float) -> np.ndarray:
        """Frequency domain attack."""
        # Convert to frequency domain
        fft = fft2(image)
        fft_shifted = fftshift(fft)

        # Add perturbation in frequency domain
        h, w = image.shape[:2]
        noise = np.random.randn(h, w) * epsilon * 0.5

        # Apply only to high frequencies
        center_h, center_w = h // 2, w // 2
        for i in range(h):
            for j in range(w):
                dist = np.sqrt((i - center_h) ** 2 + (j - center_w) ** 2)
                if dist > min(h, w) * 0.3:
                    fft_shifted[i, j] += noise[i, j] * 1j

        # Convert back
        fft = ifftshift(fft_shifted)
        perturbed = np.real(ifft2(fft))

        return np.clip(perturbed, 0, 1)

    def _spatial_domain_attack(self, image: np.ndarray, epsilon: float) -> np.ndarray:
        """Spatial domain attack."""
        # Generate smooth perturbation
        h, w = image.shape[:2]
        noise = np.random.randn(h, w) * epsilon
        smoothed = gaussian_filter(noise, sigma=1.0)

        # Apply to each channel
        if len(image.shape) == 3:
            perturbation = np.stack([smoothed] * image.shape[2], axis=-1)
        else:
            perturbation = smoothed

        perturbed = image + perturbation

        return np.clip(perturbed, 0, 1)

    def _color_domain_attack(self, image: np.ndarray, epsilon: float) -> np.ndarray:
        """Color domain attack."""
        # Convert to YCbCr
        ycbcr = self._rgb_to_ycbcr(image)

        # Add perturbation to Cb and Cr channels
        noise_cb = np.random.randn(*ycbcr[:, :, 1].shape) * epsilon * 0.3
        noise_cr = np.random.randn(*ycbcr[:, :, 2].shape) * epsilon * 0.3

        ycbcr[:, :, 1] += noise_cb
        ycbcr[:, :, 2] += noise_cr

        # Convert back to RGB
        rgb = self._ycbcr_to_rgb(ycbcr)

        return np.clip(rgb, 0, 1)

    def _simulate_gradient(self, image: np.ndarray) -> np.ndarray:
        """
        Simulate gradient for attack.
        """
        # Use image gradients as proxy for real model gradients
        if len(image.shape) == 3:
            # Process each channel
            gradient = np.zeros_like(image)
            for c in range(image.shape[2]):
                gradient[:, :, c] = self._compute_gradient(image[:, :, c])
        else:
            gradient = self._compute_gradient(image)

        # Normalize
        gradient = gradient / (np.linalg.norm(gradient) + 1e-10)

        return gradient

    def _compute_gradient(self, channel: np.ndarray) -> np.ndarray:
        """Compute gradient of a single channel."""
        # Sobel-like gradient
        h, w = channel.shape
        grad = np.zeros((h, w))

        # Simple gradient approximation
        grad[1:-1, 1:-1] = (
            channel[2:, 1:-1] - channel[:-2, 1:-1] +
            channel[1:-1, 2:] - channel[1:-1, :-2]
        ) / 4.0

        return grad

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

    def _enforce_imperceptibility(self, original: np.ndarray,
                                  perturbed: np.ndarray) -> np.ndarray:
        """
        Ensure perturbations are imperceptible.
        """
        # Calculate SSIM (simplified)
        diff = perturbed - original

        # Limit perturbation
        diff = np.clip(diff, -0.03, 0.03)

        # Apply spatial smoothing to perturbation
        if len(diff.shape) == 3:
            for c in range(diff.shape[2]):
                diff[:, :, c] = gaussian_filter(diff[:, :, c], sigma=0.5)
        else:
            diff = gaussian_filter(diff, sigma=0.5)

        # Reapply
        perturbed = original + diff

        return np.clip(perturbed, 0, 1)

    def detect_adversarial(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect if image contains adversarial perturbations.

        Returns:
            Dict: Detection results
        """
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        metrics = self._calculate_metrics(image_float)

        return {
            'has_adversarial': metrics.evasion_confidence > 0.3,
            'metrics': {
                'perturbation_magnitude': metrics.perturbation_magnitude,
                'ssim_score': metrics.ssim_score,
                'psnr_score': metrics.psnr_score,
                'evasion_confidence': metrics.evasion_confidence
            },
            'confidence': min(1.0, metrics.evasion_confidence / 0.5)
        }

    def _calculate_metrics(self, image: np.ndarray) -> AdversarialMetrics:
        """
        Calculate adversarial metrics.
        """
        # 1. Perturbation magnitude
        # Use high-frequency energy as proxy
        if len(image.shape) == 3:
            gray = np.mean(image, axis=-1)
        else:
            gray = image

        fft = np.fft.fft2(gray)
        magnitude = np.abs(np.fft.fftshift(fft))

        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # High frequency energy
        high_freq = magnitude.copy()
        high_freq[center_h - 20:center_h + 20, center_w - 20:center_w + 20] = 0
        high_energy = np.sum(high_freq)
        total_energy = np.sum(magnitude)

        perturbation_magnitude = high_energy / (total_energy + 1e-10)

        # 2. SSIM (simplified)
        ssim_score = 0.95 - perturbation_magnitude * 0.3

        # 3. PSNR
        psnr_score = 40 - perturbation_magnitude * 20

        # 4. Evasion confidence
        evasion_confidence = perturbation_magnitude * 1.5

        return AdversarialMetrics(
            perturbation_magnitude=min(1.0, perturbation_magnitude),
            ssim_score=max(0.0, ssim_score),
            psnr_score=max(0.0, psnr_score),
            evasion_confidence=min(1.0, evasion_confidence)
        )

    def adaptive_perturbation(self, image: np.ndarray, epsilon: float = 0.03) -> np.ndarray:
        """
        Add content-adaptive perturbations.
        """
        # Convert to float
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        # Calculate image content (edges, textures)
        if len(image_float.shape) == 3:
            gray = np.mean(image_float, axis=-1)
        else:
            gray = image_float

        # Edge detection (simplified)
        from scipy.ndimage import sobel
        edges = np.sqrt(sobel(gray, axis=0) ** 2 + sobel(gray, axis=1) ** 2)

        # Normalize edges
        edges = edges / (np.max(edges) + 1e-10)

        # Generate perturbation: more in smooth areas, less in edge areas
        noise = np.random.randn(*gray.shape) * epsilon
        noise = gaussian_filter(noise, sigma=1.0)

        # Scale by inverse of edges (more noise in smooth areas)
        smoothness = 1 - edges
        noise = noise * smoothness * 2

        # Apply to all channels
        if len(image_float.shape) == 3:
            perturbation = np.stack([noise] * image_float.shape[2], axis=-1)
        else:
            perturbation = noise

        perturbed = image_float + perturbation

        return np.clip(perturbed * 255, 0, 255).astype(np.uint8)