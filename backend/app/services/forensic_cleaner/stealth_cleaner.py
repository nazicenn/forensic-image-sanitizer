"""
Stealth Cleaner - Hide cleaning traces and make images appear natural.
"""

import numpy as np
import json
import random
from PIL import Image, ImageOps
from scipy.ndimage import gaussian_filter
from datetime import datetime, timedelta
import logging
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CameraMetadata:
    """Camera metadata for realistic EXIF."""
    make: str
    model: str
    lens: str
    focal_length: float
    aperture: float
    shutter_speed: str
    iso: int
    date_taken: str
    gps: Optional[Dict[str, float]] = None


@dataclass
class EditHistory:
    """Edit history simulation."""
    software: str
    version: str
    edits: List[str]
    timestamp: str


class StealthCleaner:
    """
    Hide cleaning traces and add realistic metadata.
    """

    def __init__(self):
        self.cameras = self._load_camera_profiles()
        self.edit_software = [
            'Adobe Photoshop CC',
            'Adobe Lightroom Classic',
            'Capture One Pro',
            'Affinity Photo',
            'DXO PhotoLab',
            'Luminar Neo',
            'ON1 Photo RAW'
        ]

    def _load_camera_profiles(self) -> List[CameraMetadata]:
        """Load realistic camera profiles."""
        return [
            CameraMetadata(
                make='Canon',
                model='EOS 5D Mark IV',
                lens='EF 24-70mm f/2.8L II USM',
                focal_length=35.0,
                aperture=2.8,
                shutter_speed='1/125',
                iso=400,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 40.7128, 'lon': -74.0060}
            ),
            CameraMetadata(
                make='Nikon',
                model='D850',
                lens='AF-S 24-70mm f/2.8E ED VR',
                focal_length=50.0,
                aperture=2.8,
                shutter_speed='1/250',
                iso=200,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 48.8566, 'lon': 2.3522}
            ),
            CameraMetadata(
                make='Sony',
                model='Alpha 7 III',
                lens='FE 24-70mm f/2.8 GM',
                focal_length=24.0,
                aperture=4.0,
                shutter_speed='1/60',
                iso=800,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 35.6762, 'lon': 139.6503}
            ),
            CameraMetadata(
                make='Fujifilm',
                model='X-T4',
                lens='XF 16-55mm f/2.8 R LM WR',
                focal_length=23.0,
                aperture=2.0,
                shutter_speed='1/500',
                iso=160,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 51.5074, 'lon': -0.1278}
            ),
            CameraMetadata(
                make='Panasonic',
                model='Lumix S5',
                lens='LUMIX S 24-105mm f/4 Macro OIS',
                focal_length=45.0,
                aperture=4.0,
                shutter_speed='1/100',
                iso=640,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 37.7749, 'lon': -122.4194}
            ),
            CameraMetadata(
                make='Apple',
                model='iPhone 14 Pro',
                lens='Main Camera - 24mm f/1.78',
                focal_length=6.86,
                aperture=1.78,
                shutter_speed='1/50',
                iso=100,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 40.7128, 'lon': -74.0060}
            ),
            CameraMetadata(
                make='Google',
                model='Pixel 7 Pro',
                lens='Main Camera - 25mm f/1.85',
                focal_length=6.81,
                aperture=1.85,
                shutter_speed='1/60',
                iso=150,
                date_taken=datetime.now().strftime('%Y:%m:%d %H:%M:%S'),
                gps={'lat': 37.7749, 'lon': -122.4194}
            ),
        ]

    def clean_all(self, image: np.ndarray, camera_name: str = None) -> np.ndarray:
        """
        Apply stealth mode to image.

        Args:
            image: Input image
            camera_name: Optional specific camera model

        Returns:
            np.ndarray: Stealth image
        """
        logger.info("Applying stealth mode...")

        # Convert to PIL for metadata
        if image.dtype == np.uint8:
            pil_image = Image.fromarray(image)
        else:
            pil_image = Image.fromarray((image * 255).astype(np.uint8))

        # 1. Add realistic JPEG artifacts
        image_with_artifacts = self._add_jpeg_artifacts(pil_image)

        # 2. Add realistic metadata
        metadata = self._generate_metadata(camera_name)
        image_with_metadata = self._add_metadata(image_with_artifacts, metadata)

        # 3. Add edit history
        edit_history = self._generate_edit_history()
        image_with_history = self._add_edit_history(image_with_metadata, edit_history)

        # 4. Hide cleaning traces
        image_stealth = self._hide_cleaning_traces(image_with_history)

        # Convert back to numpy
        result = np.array(image_stealth)

        # 5. Add natural noise
        result = self._add_natural_noise(result)

        return result

    def _add_jpeg_artifacts(self, image: Image.Image) -> Image.Image:
        """
        Add realistic JPEG compression artifacts.
        """
        try:
            # Save and reload with JPEG compression
            import io
            buffer = io.BytesIO()

            # Random quality between 85-95
            quality = random.randint(85, 95)
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)

            # Reload
            artifact_image = Image.open(buffer)

            # Convert back to original mode if needed
            if artifact_image.mode != image.mode:
                artifact_image = artifact_image.convert(image.mode)

            return artifact_image
        except Exception as e:
            logger.warning(f"JPEG artifact addition failed: {e}")
            return image

    def _generate_metadata(self, camera_name: str = None) -> CameraMetadata:
        """Generate realistic camera metadata."""
        if camera_name:
            # Find matching camera
            for cam in self.cameras:
                if cam_name_match(cam, camera_name):
                    return cam

        # Select random camera
        camera = random.choice(self.cameras)

        # Update timestamp
        camera.date_taken = datetime.now().strftime('%Y:%m:%d %H:%M:%S')

        return camera

    def _add_metadata(self, image: Image.Image, metadata: CameraMetadata) -> Image.Image:
        """
        Add EXIF metadata to image.
        """
        try:
            # Create EXIF data
            exif_dict = {
                '0x010f': metadata.make,  # Make
                '0x0110': metadata.model,  # Model
                '0x011a': f"{metadata.focal_length:.1f} mm",  # FocalLength
                '0x829a': metadata.shutter_speed,  # ExposureTime
                '0x829d': metadata.aperture,  # FNumber
                '0x8827': metadata.iso,  # ISOSpeedRatings
                '0x9003': metadata.date_taken,  # DateTimeOriginal
                '0x9004': metadata.date_taken,  # DateTimeDigitized
            }

            # Add GPS if available
            if metadata.gps:
                exif_dict['0x8825'] = {
                    'GPSLatitude': [metadata.gps['lat']],
                    'GPSLongitude': [metadata.gps['lon']]
                }

            # Note: Actual EXIF writing would use piexif
            # For now, return image as-is

            return image
        except Exception as e:
            logger.warning(f"Metadata addition failed: {e}")
            return image

    def _generate_edit_history(self) -> EditHistory:
        """Generate realistic edit history."""
        software = random.choice(self.edit_software)

        edits = [
            'White balance adjusted',
            'Exposure correction',
            'Contrast enhancement',
            'Color grading',
            'Sharpening applied',
            'Noise reduction',
            'Lens correction',
            'Perspective adjustment',
            'Crop and straighten'
        ]

        # Select random edits
        num_edits = random.randint(2, 5)
        selected_edits = random.sample(edits, num_edits)

        return EditHistory(
            software=software,
            version=f"{random.randint(20, 24)}.{random.randint(0, 5)}.{random.randint(0, 9)}",
            edits=selected_edits,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def _add_edit_history(self, image: Image.Image,
                          history: EditHistory) -> Image.Image:
        """
        Add edit history to image.
        """
        # For now, just return image
        # In real implementation, this would add to XMP metadata
        return image

    def _hide_cleaning_traces(self, image: Image.Image) -> Image.Image:
        """
        Hide cleaning traces by adding natural artifacts.
        """
        try:
            # Convert to numpy
            img_array = np.array(image).astype(np.float32)

            # Add subtle noise to hide processing traces
            noise = np.random.randn(*img_array.shape) * 0.5
            img_array += noise

            # Apply slight blur to smooth artifacts
            if len(img_array.shape) == 3:
                for c in range(img_array.shape[2]):
                    img_array[:, :, c] = gaussian_filter(img_array[:, :, c], sigma=0.2)
            else:
                img_array = gaussian_filter(img_array, sigma=0.2)

            # Clip and convert back
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)

            return Image.fromarray(img_array)
        except Exception as e:
            logger.warning(f"Trace hiding failed: {e}")
            return image

    def _add_natural_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Add natural-looking noise to image.
        """
        if image.dtype != np.uint8:
            return image

        # Convert to float
        img_float = image.astype(np.float32)

        # Generate noise based on image content
        noise_scale = 0.5 + np.random.random() * 0.5
        noise = np.random.randn(*img_float.shape) * noise_scale

        # Add more noise in dark areas
        if len(img_float.shape) == 3:
            luminance = np.mean(img_float, axis=-1)
            for c in range(img_float.shape[2]):
                noise[:, :, c] *= (1 - luminance / 255.0) * 2

        # Apply noise
        img_noisy = img_float + noise

        # Clip and convert back
        result = np.clip(img_noisy, 0, 255).astype(np.uint8)

        return result

    def generate_gps(self) -> Dict[str, float]:
        """Generate realistic GPS coordinates."""
        # Famous locations
        locations = [
            (40.7128, -74.0060),  # NYC
            (34.0522, -118.2437),  # LA
            (41.8781, -87.6298),  # Chicago
            (29.7604, -95.3698),  # Houston
            (37.7749, -122.4194),  # SF
            (47.6062, -122.3321),  # Seattle
            (39.9526, -75.1652),  # Philly
            (42.3601, -71.0589),  # Boston
            (32.7157, -117.1611),  # SD
            (39.7392, -104.9903),  # Denver
            (51.5074, -0.1278),  # London
            (48.8566, 2.3522),  # Paris
            (52.5200, 13.4050),  # Berlin
            (41.9028, 12.4964),  # Rome
            (40.4168, -3.7038),  # Madrid
            (35.6762, 139.6503),  # Tokyo
            (22.3193, 114.1694),  # HK
            (1.3521, 103.8198),  # Singapore
            (-33.8688, 151.2093),  # Sydney
            (-23.5505, -46.6333),  # Sao Paulo
        ]

        lat, lon = random.choice(locations)

        # Add some randomness
        lat += random.uniform(-0.01, 0.01)
        lon += random.uniform(-0.01, 0.01)

        return {'latitude': lat, 'longitude': lon}

    def get_camera_list(self) -> List[str]:
        """Get list of available cameras."""
        return [f"{cam.make} {cam.model}" for cam in self.cameras]

    def get_camera_metadata(self, camera_name: str) -> Optional[CameraMetadata]:
        """Get metadata for a specific camera."""
        for cam in self.cameras:
            if cam_name_match(cam, camera_name):
                return cam
        return None


def cam_name_match(cam: CameraMetadata, name: str) -> bool:
    """Check if camera name matches."""
    full_name = f"{cam.make} {cam.model}"
    return name.lower() in full_name.lower() or full_name.lower() in name.lower()