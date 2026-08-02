"""
PRNU Cleaner - Add realistic sensor noise (Photo Response Non-Uniformity) to images.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
import logging
import json
import os
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CameraProfile:
    """Camera sensor profile."""
    name: str
    manufacturer: str
    model: str
    iso_range: List[int]
    noise_params: Dict[str, Any]
    prnu_pattern: Optional[np.ndarray] = None
    vignette_params: Dict[str, float] = field(default_factory=lambda: {
        'center_x': 0.5,
        'center_y': 0.5,
        'falloff': 0.5
    })


class PRNUCleaner:
    """Add realistic sensor noise to images."""

    def __init__(self):
        self.camera_profiles = self._load_camera_profiles()
        self.default_iso = 400

    def _load_camera_profiles(self) -> Dict[str, CameraProfile]:
        """Load camera profiles."""
        profiles = {
            'canon_5d_mark_iv': CameraProfile(
                name='canon_5d_mark_iv',
                manufacturer='Canon',
                model='EOS 5D Mark IV',
                iso_range=[100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600],
                noise_params={
                    'poisson_scale': 0.01,
                    'gaussian_scale': 0.005,
                    'prnu_strength': 0.003
                }
            ),
            'nikon_d850': CameraProfile(
                name='nikon_d850',
                manufacturer='Nikon',
                model='D850',
                iso_range=[64, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600],
                noise_params={
                    'poisson_scale': 0.008,
                    'gaussian_scale': 0.004,
                    'prnu_strength': 0.002
                }
            ),
            'sony_a7iii': CameraProfile(
                name='sony_a7iii',
                manufacturer='Sony',
                model='Alpha 7 III',
                iso_range=[100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200],
                noise_params={
                    'poisson_scale': 0.009,
                    'gaussian_scale': 0.006,
                    'prnu_strength': 0.004
                }
            ),
            'fuji_xt4': CameraProfile(
                name='fuji_xt4',
                manufacturer='Fujifilm',
                model='X-T4',
                iso_range=[160, 200, 400, 800, 1600, 3200, 6400, 12800, 25600],
                noise_params={
                    'poisson_scale': 0.012,
                    'gaussian_scale': 0.007,
                    'prnu_strength': 0.005
                }
            ),
            'panasonic_lumix_s5': CameraProfile(
                name='panasonic_lumix_s5',
                manufacturer='Panasonic',
                model='Lumix S5',
                iso_range=[100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200],
                noise_params={
                    'poisson_scale': 0.01,
                    'gaussian_scale': 0.005,
                    'prnu_strength': 0.003
                }
            ),
            'iphone_14_pro': CameraProfile(
                name='iphone_14_pro',
                manufacturer='Apple',
                model='iPhone 14 Pro',
                iso_range=[25, 50, 100, 200, 400, 800, 1600, 3200],
                noise_params={
                    'poisson_scale': 0.02,
                    'gaussian_scale': 0.015,
                    'prnu_strength': 0.008
                }
            ),
            'google_pixel_7': CameraProfile(
                name='google_pixel_7',
                manufacturer='Google',
                model='Pixel 7',
                iso_range=[50, 100, 200, 400, 800, 1600, 3200],
                noise_params={
                    'poisson_scale': 0.018,
                    'gaussian_scale': 0.012,
                    'prnu_strength': 0.007
                }
            ),
            'samsung_galaxy_s23': CameraProfile(
                name='samsung_galaxy_s23',
                manufacturer='Samsung',
                model='Galaxy S23',
                iso_range=[50, 100, 200, 400, 800, 1600, 3200],
                noise_params={
                    'poisson_scale': 0.015,
                    'gaussian_scale': 0.01,
                    'prnu_strength': 0.006
                }
            ),
        }
        return profiles

    def add_prnu(self, image: np.ndarray, camera_name: str = 'canon_5d_mark_iv',
                 iso: int = 400, strength: float = 1.0) -> np.ndarray:
        """
        Add PRNU (sensor noise) to an image.

        Args:
            image: Input image as numpy array (H, W, C)
            camera_name: Camera model name
            iso: ISO value
            strength: Noise strength multiplier

        Returns:
            np.ndarray: Image with PRNU added
        """
        logger.info(f"Adding PRNU with camera={camera_name}, iso={iso}")

        # Get camera profile
        profile = self.camera_profiles.get(camera_name)
        if not profile:
            logger.warning(f"Camera {camera_name} not found, using default")
            profile = self.camera_profiles['canon_5d_mark_iv']

        # Convert to float
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        # 1. Add Poisson noise (shot noise)
        image_noisy = self._add_poisson_noise(
            image_float, 
            profile.noise_params['poisson_scale'] * strength * (iso / 400)
        )

        # 2. Add Gaussian noise (read noise)
        image_noisy = self._add_gaussian_noise(
            image_noisy,
            profile.noise_params['gaussian_scale'] * strength * np.sqrt(iso / 400)
        )

        # 3. Add PRNU fingerprint
        if profile.prnu_pattern is not None:
            image_noisy = self._add_prnu_fingerprint(
                image_noisy,
                profile.prnu_pattern,
                profile.noise_params['prnu_strength'] * strength
            )

        # 4. Add vignette
        image_noisy = self._add_vignette(
            image_noisy,
            profile.vignette_params
        )

        # 5. Add hot pixels
        image_noisy = self._add_hot_pixels(image_noisy, iso)

        # Convert back to uint8
        result = np.clip(image_noisy * 255, 0, 255).astype(np.uint8)

        return result

    def _add_poisson_noise(self, image: np.ndarray, scale: float) -> np.ndarray:
        """Add Poisson (shot) noise."""
        # Poisson noise is signal-dependent
        noise = np.random.poisson(image * scale) / scale
        return image + (noise - image) * 0.5

    def _add_gaussian_noise(self, image: np.ndarray, scale: float) -> np.ndarray:
        """Add Gaussian (read) noise."""
        noise = np.random.randn(*image.shape) * scale
        return image + noise

    def _add_prnu_fingerprint(self, image: np.ndarray, pattern: np.ndarray,
                              strength: float) -> np.ndarray:
        """Add PRNU fingerprint pattern."""
        # Resize pattern to match image if needed
        if pattern.shape[:2] != image.shape[:2]:
            from skimage.transform import resize
            pattern_resized = resize(pattern, image.shape[:2], mode='reflect')
        else:
            pattern_resized = pattern

        # Ensure pattern has same number of channels
        if len(pattern_resized.shape) == 2 and len(image.shape) == 3:
            pattern_resized = np.stack([pattern_resized] * image.shape[2], axis=-1)

        return image + pattern_resized * strength

    def _add_vignette(self, image: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Add vignette (lens shading) effect."""
        h, w = image.shape[:2]
        center_x = params.get('center_x', 0.5) * w
        center_y = params.get('center_y', 0.5) * h
        falloff = params.get('falloff', 0.5)

        # Create distance mask
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        max_distance = np.sqrt((w / 2) ** 2 + (h / 2) ** 2)

        # Vignette mask: 1 at center, 0.3 at edges
        vignette = 1 - (distance / max_distance) * falloff * 0.7
        vignette = np.clip(vignette, 0.3, 1.0)

        # Apply vignette to each channel
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                image[:, :, c] *= vignette
        else:
            image *= vignette

        return image

    def _add_hot_pixels(self, image: np.ndarray, iso: int) -> np.ndarray:
        """Add hot pixels (defective pixels)."""
        h, w = image.shape[:2]

        # Number of hot pixels depends on ISO
        num_hot_pixels = int(h * w * 0.0001 * (iso / 400))

        if num_hot_pixels > 0:
            # Random positions
            hot_pixel_mask = np.random.rand(h, w) < (num_hot_pixels / (h * w))

            # Hot pixels values (bright)
            hot_values = np.random.uniform(0.8, 1.0, (np.sum(hot_pixel_mask),))

            if len(image.shape) == 3:
                for c in range(image.shape[2]):
                    image[:, :, c][hot_pixel_mask] = hot_values
            else:
                image[hot_pixel_mask] = hot_values

        return image

    def apply_bayer_pattern(self, image: np.ndarray, pattern: str = 'RGGB') -> np.ndarray:
        """
        Apply Bayer pattern filter (color filter array simulation).

        Args:
            image: Input image
            pattern: Bayer pattern (RGGB, BGGR, GBRG, GRBG)

        Returns:
            np.ndarray: Image with Bayer pattern applied
        """
        h, w = image.shape[:2]

        # Create Bayer pattern mask
        bayer_mask = np.zeros((h, w), dtype=np.float32)

        if pattern == 'RGGB':
            # Row 0: R G R G ...
            # Row 1: G B G B ...
            for i in range(h):
                for j in range(w):
                    if i % 2 == 0 and j % 2 == 0:
                        bayer_mask[i, j] = 1.0  # R
                    elif i % 2 == 0 and j % 2 == 1:
                        bayer_mask[i, j] = 0.5  # G
                    elif i % 2 == 1 and j % 2 == 0:
                        bayer_mask[i, j] = 0.5  # G
                    else:
                        bayer_mask[i, j] = 0.0  # B

        elif pattern == 'BGGR':
            for i in range(h):
                for j in range(w):
                    if i % 2 == 0 and j % 2 == 0:
                        bayer_mask[i, j] = 0.0  # B
                    elif i % 2 == 0 and j % 2 == 1:
                        bayer_mask[i, j] = 0.5  # G
                    elif i % 2 == 1 and j % 2 == 0:
                        bayer_mask[i, j] = 0.5  # G
                    else:
                        bayer_mask[i, j] = 1.0  # R

        # Apply mask to each channel
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                image[:, :, c] *= bayer_mask
        else:
            image *= bayer_mask

        return image

    def generate_prnu_pattern(self, shape: Tuple[int, int],
                              camera_name: str = 'canon_5d_mark_iv') -> np.ndarray:
        """
        Generate a PRNU fingerprint pattern for a specific camera.

        Args:
            shape: (height, width) of the pattern
            camera_name: Camera model name

        Returns:
            np.ndarray: PRNU pattern
        """
        h, w = shape

        # Get camera profile
        profile = self.camera_profiles.get(camera_name)
        if not profile:
            profile = self.camera_profiles['canon_5d_mark_iv']

        # Generate random pattern with spatial correlation
        pattern = np.random.randn(h, w)

        # Add spatial correlation (smoothness)
        pattern = gaussian_filter(pattern, sigma=1.0)

        # Normalize
        pattern = (pattern - np.mean(pattern)) / np.std(pattern)

        # Scale based on camera
        pattern *= profile.noise_params.get('prnu_strength', 0.003)

        # Store in profile
        profile.prnu_pattern = pattern

        return pattern

    def get_camera_list(self) -> List[str]:
        """Get list of available camera profiles."""
        return list(self.camera_profiles.keys())

    def get_camera_info(self, camera_name: str) -> Dict[str, Any]:
        """Get information about a camera profile."""
        profile = self.camera_profiles.get(camera_name)
        if not profile:
            return {}

        return {
            'name': profile.name,
            'manufacturer': profile.manufacturer,
            'model': profile.model,
            'iso_range': profile.iso_range,
            'noise_params': profile.noise_params
        }

    def add_adaptive_noise(self, image: np.ndarray, iso: int = 400) -> np.ndarray:
        """
        Add content-adaptive noise (more noise in dark areas).

        Args:
            image: Input image
            iso: ISO value

        Returns:
            np.ndarray: Image with adaptive noise
        """
        # Convert to float
        if image.dtype == np.uint8:
            image_float = image.astype(np.float32) / 255.0
        else:
            image_float = image.astype(np.float32)

        # Calculate luminance
        if len(image_float.shape) == 3:
            luminance = np.mean(image_float, axis=-1)
        else:
            luminance = image_float

        # Noise scale depends on luminance (more noise in dark areas)
        noise_scale = 1 - luminance
        noise_scale = np.clip(noise_scale, 0.1, 1.0)

        # Generate noise
        noise = np.random.randn(*image_float.shape) * 0.02 * (iso / 400)

        # Apply adaptive scaling
        if len(image_float.shape) == 3:
            for c in range(image_float.shape[2]):
                image_float[:, :, c] += noise[:, :, c] * noise_scale
        else:
            image_float += noise * noise_scale

        # Convert back to uint8
        result = np.clip(image_float * 255, 0, 255).astype(np.uint8)

        return result