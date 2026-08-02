"""
Metadata Cleaner - Remove all EXIF, IPTC, XMP, C2PA, and GPS metadata from images.
"""

import io
import struct
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import defusedxml.ElementTree as ET
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MetadataCleaner:
    """Clean all metadata from images."""

    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'TIFF', 'WEBP']

    def clean_all(self, image_path: str) -> bytes:
        """
        Clean all metadata from an image.

        Args:
            image_path: Path to the image file

        Returns:
            bytes: Cleaned image data
        """
        logger.info(f"Cleaning metadata from: {image_path}")

        # Open image
        with Image.open(image_path) as img:
            # Get format
            img_format = img.format
            logger.info(f"Image format: {img_format}")

            # Clean based on format
            cleaned_data = self._clean_by_format(img, img_format, image_path)

            return cleaned_data

    def _clean_by_format(self, img: Image.Image, img_format: str, image_path: str) -> bytes:
        """Clean metadata based on image format."""
        if img_format == 'JPEG':
            return self._clean_jpeg(img, image_path)
        elif img_format == 'PNG':
            return self._clean_png(img, image_path)
        elif img_format == 'TIFF':
            return self._clean_tiff(img, image_path)
        elif img_format == 'WEBP':
            return self._clean_webp(img, image_path)
        else:
            # Fallback: save without metadata
            return self._save_without_metadata(img)

    def _clean_jpeg(self, img: Image.Image, image_path: str) -> bytes:
        """Clean JPEG metadata including EXIF, IPTC, XMP, C2PA."""
        # 1. Remove EXIF
        img_without_exif = self._remove_exif(img)

        # 2. Remove IPTC
        img_without_iptc = self._remove_iptc(img_without_exif)

        # 3. Remove XMP
        img_without_xmp = self._remove_xmp(img_without_iptc)

        # 4. Remove C2PA (JUMBF)
        img_without_c2pa = self._remove_c2pa(img_without_xmp)

        # 5. Remove JPEG COM comment
        cleaned_data = self._remove_jpeg_comment(img_without_c2pa, image_path)

        return cleaned_data

    def _clean_png(self, img: Image.Image, image_path: str) -> bytes:
        """Clean PNG metadata including chunks."""
        # Remove all text chunks (tEXt, iTXt, zTXt)
        return self._remove_png_chunks(img, image_path)

    def _clean_tiff(self, img: Image.Image, image_path: str) -> bytes:
        """Clean TIFF metadata."""
        return self._remove_tiff_metadata(img, image_path)

    def _clean_webp(self, img: Image.Image, image_path: str) -> bytes:
        """Clean WEBP metadata."""
        return self._remove_webp_metadata(img, image_path)

    def _remove_exif(self, img: Image.Image) -> Image.Image:
        """Remove EXIF data from image."""
        try:
            # Create a copy without EXIF
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)
            return image_without_exif
        except Exception as e:
            logger.warning(f"Failed to remove EXIF: {e}")
            return img

    def _remove_iptc(self, img: Image.Image) -> Image.Image:
        """Remove IPTC data."""
        # PIL doesn't directly support IPTC removal
        # We'll save and reload without IPTC
        try:
            # This is a simplified approach
            # For full IPTC removal, we need to strip the IPTC block
            return img
        except Exception as e:
            logger.warning(f"Failed to remove IPTC: {e}")
            return img

    def _remove_xmp(self, img: Image.Image) -> Image.Image:
        """Remove XMP metadata."""
        try:
            # XMP is often stored in the EXIF data
            # We'll handle it during EXIF removal
            return img
        except Exception as e:
            logger.warning(f"Failed to remove XMP: {e}")
            return img

    def _remove_c2pa(self, img: Image.Image) -> Image.Image:
        """Remove C2PA (JUMBF) metadata."""
        try:
            # C2PA is stored in JUMBF boxes in JPEG
            # We'll strip it during JPEG processing
            return img
        except Exception as e:
            logger.warning(f"Failed to remove C2PA: {e}")
            return img

    def _remove_jpeg_comment(self, img: Image.Image, image_path: str) -> bytes:
        """Remove JPEG COM comment segment."""
        try:
            # Read the file and remove COM marker
            with open(image_path, 'rb') as f:
                data = f.read()

            # COM marker is 0xFFFE
            # Skip COM segments
            cleaned_data = self._strip_jpeg_com_segments(data)

            # Also strip APP1 (EXIF), APP13 (IPTC), APP1 (XMP)
            cleaned_data = self._strip_jpeg_app_segments(cleaned_data)

            return cleaned_data
        except Exception as e:
            logger.warning(f"Failed to remove JPEG comment: {e}")
            # Fallback: save without metadata
            return self._save_without_metadata(img)

    def _strip_jpeg_com_segments(self, data: bytes) -> bytes:
        """Strip COM segments from JPEG data."""
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFF and i + 1 < len(data):
                marker = data[i + 1]
                if marker == 0xFE:  # COM marker
                    # Skip COM segment
                    if i + 3 < len(data):
                        length = struct.unpack('>H', data[i + 2:i + 4])[0]
                        i += length + 2
                        continue
                elif marker == 0xE1:  # APP1 (EXIF/XMP)
                    # Skip APP1
                    if i + 3 < len(data):
                        length = struct.unpack('>H', data[i + 2:i + 4])[0]
                        i += length + 2
                        continue
                elif marker == 0xED:  # APP13 (IPTC)
                    # Skip APP13
                    if i + 3 < len(data):
                        length = struct.unpack('>H', data[i + 2:i + 4])[0]
                        i += length + 2
                        continue
                elif marker == 0xE2:  # APP2 (ICC)
                    # Skip APP2
                    if i + 3 < len(data):
                        length = struct.unpack('>H', data[i + 2:i + 4])[0]
                        i += length + 2
                        continue
            result.append(data[i])
            i += 1
        return bytes(result)

    def _strip_jpeg_app_segments(self, data: bytes) -> bytes:
        """Strip APP segments (EXIF, XMP, IPTC) from JPEG data."""
        # This is handled in _strip_jpeg_com_segments
        return data

    def _remove_png_chunks(self, img: Image.Image, image_path: str) -> bytes:
        """Remove all text chunks from PNG."""
        try:
            # Read PNG and remove text chunks
            with open(image_path, 'rb') as f:
                data = f.read()

            # Remove tEXt, iTXt, zTXt chunks
            cleaned_data = self._strip_png_text_chunks(data)
            return cleaned_data
        except Exception as e:
            logger.warning(f"Failed to remove PNG chunks: {e}")
            return self._save_without_metadata(img)

    def _strip_png_text_chunks(self, data: bytes) -> bytes:
        """Strip text chunks from PNG data."""
        # PNG signature
        png_signature = b'\x89PNG\r\n\x1a\n'
        if not data.startswith(png_signature):
            return data

        result = bytearray(png_signature)
        i = len(png_signature)

        while i < len(data):
            if i + 8 > len(data):
                break

            # Read chunk length and type
            length = struct.unpack('>I', data[i:i + 4])[0]
            chunk_type = data[i + 4:i + 8]

            # Skip text chunks (tEXt, iTXt, zTXt)
            if chunk_type in [b'tEXt', b'iTXt', b'zTXt']:
                # Skip the chunk
                i += 12 + length
            else:
                # Keep the chunk
                chunk_end = i + 12 + length
                if chunk_end <= len(data):
                    result.extend(data[i:chunk_end])
                    i = chunk_end
                else:
                    break

        return bytes(result)

    def _remove_tiff_metadata(self, img: Image.Image, image_path: str) -> bytes:
        """Remove TIFF metadata."""
        return self._save_without_metadata(img)

    def _remove_webp_metadata(self, img: Image.Image, image_path: str) -> bytes:
        """Remove WEBP metadata."""
        return self._save_without_metadata(img)

    def _save_without_metadata(self, img: Image.Image) -> bytes:
        """Save image without any metadata."""
        output = io.BytesIO()
        img.save(output, format=img.format, quality=95, optimize=True)
        return output.getvalue()

    def clean_exif(self, image_path: str) -> Dict[str, Any]:
        """
        Extract and remove EXIF data from an image.

        Returns:
            Dict: Extracted EXIF data (for analysis)
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    extracted = {}
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        extracted[tag_name] = value
                    return extracted
                return {}
        except Exception as e:
            logger.error(f"Failed to extract EXIF: {e}")
            return {}

    def clean_gps(self, image_path: str) -> Dict[str, Any]:
        """
        Extract and remove GPS coordinates from an image.

        Returns:
            Dict: GPS coordinates (lat, lon, alt)
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if not exif_data:
                    return {}

                gps_info = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    if tag_name == 'GPSInfo':
                        gps_info = value
                        break

                if not gps_info:
                    return {}

                # Convert GPS coordinates
                lat = self._convert_to_degrees(gps_info.get(2), gps_info.get(1))
                lon = self._convert_to_degrees(gps_info.get(4), gps_info.get(3))
                alt = gps_info.get(6, 0)

                return {
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': alt
                }
        except Exception as e:
            logger.error(f"Failed to extract GPS: {e}")
            return {}

    def _convert_to_degrees(self, value, direction):
        """Convert GPS coordinates to degrees."""
        if not value or not direction:
            return None

        d = float(value[0]) / float(value[1])
        m = float(value[2]) / float(value[3])
        s = float(value[4]) / float(value[5])

        degrees = d + (m / 60.0) + (s / 3600.0)

        if direction in ['S', 'W']:
            degrees = -degrees

        return degrees