"""
Frequency Cleaner - Remove AI-generated frequency artifacts from images.
"""

import numpy as np
from scipy.fft import fft2, ifft2, fftshift, ifftshift
from scipy.ndimage import gaussian_filter
from scipy.signal import butter, filtfilt
from PIL import Image
import cv2
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class FrequencyCleaner:
    """Clean frequency domain artifacts from images."""

    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'TIFF', 'WEBP']

    def clean_all(self, image_array: np.ndarray) -> np.ndarray:
        """
        Clean all frequency artifacts from an image.

        Args:
            image_array: Input image as numpy array (H, W, C)

        Returns:
            np.ndarray: Cleaned image
        """
        logger.info("Cleaning frequency artifacts...")

        # Convert to float for processing
        if image_array.dtype == np.uint8:
            image_float = image_array.astype(np.float32) / 255.0
        else:
            image_float = image_array.astype(np.float32)

        # Process each channel separately
        if len(image_float.shape) == 3:
            channels = []
            for c in range(image_float.shape[2]):
                channel = self._clean_channel(image_float[:, :, c])
                channels.append(channel)
            cleaned = np.stack(channels, axis=-1)
        else:
            cleaned = self._clean_channel(image_float)

        # Convert back to uint8
        cleaned = np.clip(cleaned * 255, 0, 255).astype(np.uint8)

        return cleaned

    def _clean_channel(self, channel: np.ndarray) -> np.ndarray:
        """Clean a single channel."""
        # 1. FFT transform
        fft_data = fft2(channel)

        # 2. Detect and remove checkerboard artifacts
        fft_data = self._remove_checkerboard(fft_data)

        # 3. Detect and remove grid artifacts
        fft_data = self._remove_grid_artifacts(fft_data)

        # 4. Apply low-pass filter
        fft_data = self._apply_low_pass(fft_data)

        # 5. Smooth spectrum
        fft_data = self._smooth_spectrum(fft_data)

        # 6. Inverse FFT
        cleaned = np.real(ifft2(fft_data))

        return cleaned

    def detect_checkerboard(self, fft_data: np.ndarray) -> Dict[str, Any]:
        """
        Detect checkerboard artifacts at (π, π) frequency.

        Returns:
            Dict: Detection results with peaks and confidence
        """
        # Shift zero frequency to center
        fft_shifted = fftshift(fft_data)
        magnitude = np.abs(fft_shifted)

        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Check for peaks at (π, π) - corners of the frequency spectrum
        # In shifted spectrum, (π, π) corresponds to corners
        corners = [
            (0, 0),
            (0, w - 1),
            (h - 1, 0),
            (h - 1, w - 1)
        ]

        peaks = []
        for corner_h, corner_w in corners:
            # Check small region around corner
            region_size = 5
            h_start = max(0, corner_h - region_size)
            h_end = min(h, corner_h + region_size + 1)
            w_start = max(0, corner_w - region_size)
            w_end = min(w, corner_w + region_size + 1)

            region = magnitude[h_start:h_end, w_start:w_end]
            if region.size > 0:
                peak_value = np.max(region)
                if peak_value > np.mean(magnitude) * 2:
                    peaks.append({
                        'position': (corner_h, corner_w),
                        'value': float(peak_value),
                        'relative': float(peak_value / np.mean(magnitude))
                    })

        return {
            'has_checkerboard': len(peaks) > 0,
            'peaks': peaks,
            'confidence': len(peaks) / 4.0
        }

    def _remove_checkerboard(self, fft_data: np.ndarray) -> np.ndarray:
        """
        Remove checkerboard artifacts.
        """
        # Shift zero frequency to center
        fft_shifted = fftshift(fft_data)
        magnitude = np.abs(fft_shifted)

        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Suppress corners (where checkerboard artifacts appear)
        corner_size = 3
        for corner_h in [0, h - 1]:
            for corner_w in [0, w - 1]:
                # Get the region around corner
                h_start = max(0, corner_h - corner_size)
                h_end = min(h, corner_h + corner_size + 1)
                w_start = max(0, corner_w - corner_size)
                w_end = min(w, corner_w + corner_size + 1)

                # Suppress by reducing magnitude
                region_mean = np.mean(magnitude)
                fft_shifted[h_start:h_end, w_start:w_end] = fft_shifted[h_start:h_end, w_start:w_end] * 0.1

        # Shift back
        return ifftshift(fft_shifted)

    def detect_grid_artifacts(self, fft_data: np.ndarray) -> Dict[str, Any]:
        """
        Detect grid artifacts at specific harmonics.

        Returns:
            Dict: Detection results
        """
        fft_shifted = fftshift(fft_data)
        magnitude = np.abs(fft_shifted)

        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Check horizontal and vertical lines
        horizontal_line = magnitude[center_h, :]
        vertical_line = magnitude[:, center_w]

        # Find peaks in lines
        from scipy.signal import find_peaks

        h_peaks, _ = find_peaks(horizontal_line, height=np.mean(horizontal_line) * 1.5)
        v_peaks, _ = find_peaks(vertical_line, height=np.mean(vertical_line) * 1.5)

        # Filter peaks that are not at center
        h_peaks = [p for p in h_peaks if abs(p - center_w) > 10]
        v_peaks = [p for p in v_peaks if abs(p - center_h) > 10]

        return {
            'has_grid': len(h_peaks) > 2 or len(v_peaks) > 2,
            'horizontal_peaks': len(h_peaks),
            'vertical_peaks': len(v_peaks),
            'confidence': min(1.0, (len(h_peaks) + len(v_peaks)) / 20.0)
        }

    def _remove_grid_artifacts(self, fft_data: np.ndarray) -> np.ndarray:
        """
        Remove grid artifacts by suppressing line frequencies.
        """
        fft_shifted = fftshift(fft_data)
        magnitude = np.abs(fft_shifted)

        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Suppress horizontal and vertical lines
        line_width = 2
        for i in range(-line_width, line_width + 1):
            # Horizontal line
            row_idx = center_h + i
            if 0 <= row_idx < h:
                fft_shifted[row_idx, :] = fft_shifted[row_idx, :] * 0.3

            # Vertical line
            col_idx = center_w + i
            if 0 <= col_idx < w:
                fft_shifted[:, col_idx] = fft_shifted[:, col_idx] * 0.3

        return ifftshift(fft_shifted)

    def analyze_spectrum(self, fft_data: np.ndarray) -> Dict[str, Any]:
        """
        Analyze frequency spectrum for 1/f anomalies.

        Returns:
            Dict: Analysis results
        """
        magnitude = np.abs(fft_data)
        magnitude_shifted = fftshift(magnitude)

        h, w = magnitude_shifted.shape
        center_h, center_w = h // 2, w // 2

        # Calculate radial power spectrum
        max_radius = min(center_h, center_w)
        radii = np.arange(1, max_radius)
        radial_power = []

        for r in radii:
            # Create mask for circle with radius r
            y, x = np.ogrid[:h, :w]
            mask = (x - center_w) ** 2 + (y - center_h) ** 2 <= r ** 2
            mask_next = (x - center_w) ** 2 + (y - center_h) ** 2 <= (r + 1) ** 2
            ring = mask_next & ~mask

            if np.sum(ring) > 0:
                power = np.mean(magnitude_shifted[ring])
                radial_power.append(power)
            else:
                radial_power.append(0)

        # Check if spectrum follows 1/f pattern
        if len(radial_power) > 10:
            # Fit to 1/f
            log_radii = np.log(radii)
            log_power = np.log(np.array(radial_power) + 1e-10)

            # Remove zeros and infs
            valid = np.isfinite(log_power) & np.isfinite(log_radii)
            if np.sum(valid) > 5:
                from scipy.stats import linregress
                slope, intercept, r_value, p_value, std_err = linregress(
                    log_radii[valid], log_power[valid]
                )

                return {
                    '1f_slope': float(slope),
                    'r_squared': float(r_value ** 2),
                    'anomaly_detected': abs(slope + 1) > 0.3  # 1/f should have slope ~ -1
                }

        return {'1f_slope': 0, 'r_squared': 0, 'anomaly_detected': False}

    def _apply_low_pass(self, fft_data: np.ndarray) -> np.ndarray:
        """
        Apply low-pass filter to remove high-frequency noise.
        """
        fft_shifted = fftshift(fft_data)
        h, w = fft_shifted.shape
        center_h, center_w = h // 2, w // 2

        # Create Gaussian low-pass filter
        sigma = min(h, w) * 0.15
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_w) ** 2 + (y - center_h) ** 2)
        gaussian = np.exp(-(distance ** 2) / (2 * sigma ** 2))

        # Apply filter
        fft_filtered = fft_shifted * gaussian

        return ifftshift(fft_filtered)

    def _smooth_spectrum(self, fft_data: np.ndarray) -> np.ndarray:
        """
        Smooth the frequency spectrum.
        """
        fft_shifted = fftshift(fft_data)
        magnitude = np.abs(fft_shifted)
        phase = np.angle(fft_shifted)

        # Smooth magnitude
        magnitude_smoothed = gaussian_filter(magnitude, sigma=0.5)

        # Reconstruct
        fft_smoothed = magnitude_smoothed * np.exp(1j * phase)

        return ifftshift(fft_smoothed)

    def resample(self, image: np.ndarray, shift: float = 0.3) -> np.ndarray:
        """
        Resample image by subpixel shift to remove artifacts.

        Args:
            image: Input image
            shift: Subpixel shift amount (0.1 - 0.5)

        Returns:
            np.ndarray: Resampled image
        """
        h, w = image.shape[:2]

        # Create affine transformation matrix for subpixel shift
        from scipy.ndimage import affine_transform

        # Shift matrix
        shift_matrix = np.array([
            [1, 0, shift],
            [0, 1, shift],
            [0, 0, 1]
        ])

        # Apply transform
        if len(image.shape) == 3:
            channels = []
            for c in range(image.shape[2]):
                channel = affine_transform(
                    image[:, :, c],
                    shift_matrix[:2, :2],
                    offset=shift_matrix[:2, 2],
                    order=1  # Bilinear interpolation
                )
                channels.append(channel)
            resampled = np.stack(channels, axis=-1)
        else:
            resampled = affine_transform(
                image,
                shift_matrix[:2, :2],
                offset=shift_matrix[:2, 2],
                order=1
            )

        return resampled