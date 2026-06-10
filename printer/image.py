"""Image processing utilities for thermal receipt printers."""

import base64
import io
from pathlib import Path
from typing import Literal

import requests
from PIL import Image


class ImageProcessor:
    """Handles image loading, preprocessing, and formatting for thermal printing."""

    def __init__(self, max_width: int = 531):
        """
        Initialize image processor.

        Args:
            max_width: Maximum image width in pixels (default: 531px for TM-T88IV)
        """
        self.max_width = max_width

    def load_image(self, source: str | Path | Image.Image) -> Image.Image:
        """
        Load an image from various sources.

        Args:
            source: Can be:
                - Local file path (str or Path)
                - URL (str starting with 'http://' or 'https://')
                - Base64 string (str starting with 'data:image/'
                  or just the base64 data)
                - PIL Image object (returned as-is)

        Returns:
            PIL Image object

        Raises:
            ValueError: If source type is invalid
            FileNotFoundError: If local file doesn't exist
            requests.RequestException: If URL fetch fails
        """
        # Already a PIL Image
        if isinstance(source, Image.Image):
            return source

        source_str = str(source)

        # URL
        if source_str.startswith(("http://", "https://")):
            return self._load_from_url(source_str)

        # Base64
        elif source_str.startswith("data:image/") or self._is_base64(source_str):
            return self._load_from_base64(source_str)

        # Local file
        else:
            return self._load_from_file(source_str)

    def _load_from_file(self, path: str) -> Image.Image:
        """Load image from local file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        return Image.open(file_path)

    def _load_from_url(self, url: str) -> Image.Image:
        """Load image from URL."""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))

    def _load_from_base64(self, data: str) -> Image.Image:
        """Load image from base64 string."""
        # Strip data URL prefix if present
        if data.startswith("data:image/"):
            data = data.split(",", 1)[1]

        # Decode base64
        image_data = base64.b64decode(data)
        return Image.open(io.BytesIO(image_data))

    def _is_base64(self, s: str) -> bool:
        """Check if string looks like base64 data."""
        if len(s) < 10:
            return False
        # Simple heuristic: base64 uses A-Za-z0-9+/= and is usually fairly long
        return all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            for c in s[:100]
        )

    def resize(
        self,
        image: Image.Image,
        target_width: int | None = None,
        target_height: int | None = None,
        maintain_aspect: bool = True,
        allow_upscale: bool = False,
    ) -> Image.Image:
        """
        Resize image to fit printer width.

        Args:
            image: PIL Image to resize
            target_width: Target width in pixels (default: self.max_width)
            target_height: Target height in pixels (None = auto from aspect ratio)
            maintain_aspect: Whether to maintain aspect ratio
            allow_upscale: Whether images smaller than target can be enlarged

        Returns:
            Resized PIL Image
        """
        if target_width is None:
            target_width = self.max_width

        # If image already fits and upscaling is disabled, keep original size.
        if (
            not allow_upscale
            and image.width <= target_width
            and (target_height is None or image.height <= target_height)
        ):
            return image

        if maintain_aspect:
            # Calculate height maintaining aspect ratio
            aspect_ratio = image.height / image.width
            new_width = (
                target_width if allow_upscale else min(image.width, target_width)
            )
            new_height = int(new_width * aspect_ratio)

            if target_height and new_height > target_height:
                new_height = target_height
                new_width = int(new_height / aspect_ratio)
        else:
            new_width = target_width
            new_height = target_height or image.height

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def rotate(
        self, image: Image.Image, degrees: float, expand: bool = True
    ) -> Image.Image:
        """
        Rotate image by specified degrees.

        Args:
            image: PIL Image to rotate
            degrees: Rotation angle in degrees (counter-clockwise)
            expand: If True, expand output to fit entire rotated image

        Returns:
            Rotated PIL Image
        """
        return image.rotate(degrees, expand=expand, resample=Image.Resampling.BICUBIC)

    def convert_to_printable(self, image: Image.Image) -> Image.Image:
        """
        Convert image to format suitable for thermal printing (grayscale/1-bit).

        Note: escpos library handles final dithering, but we ensure proper mode.

        Args:
            image: PIL Image to convert

        Returns:
            Converted PIL Image in RGB or L mode
        """
        # Convert to RGB if not already (escpos can handle RGB or L)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        return image

    def add_horizontal_padding(
        self,
        image: Image.Image,
        alignment: Literal["left", "center", "right"] = "left",
        canvas_width: int | None = None,
    ) -> Image.Image:
        """
        Add horizontal padding to align image on canvas.

        Args:
            image: PIL Image to pad
            alignment: Alignment ('left', 'center', 'right')
            canvas_width: Total canvas width (default: self.max_width)

        Returns:
            Padded PIL Image
        """
        if canvas_width is None:
            canvas_width = self.max_width

        if image.width >= canvas_width:
            return image

        # Create white canvas
        canvas = Image.new("RGB", (canvas_width, image.height), "white")

        # Calculate x position based on alignment
        if alignment == "center":
            x = (canvas_width - image.width) // 2
        elif alignment == "right":
            x = canvas_width - image.width
        else:  # left
            x = 0

        # Paste image onto canvas
        canvas.paste(image, (x, 0))
        return canvas

    def combine_horizontal(
        self,
        image1: Image.Image,
        image2: Image.Image,
        spacing: int = 10,
        max_width: int | None = None,
    ) -> Image.Image:
        """
        Combine two images side by side.

        Args:
            image1: First image (left)
            image2: Second image (right)
            spacing: Spacing between images in pixels
            max_width: Maximum total width (default: self.max_width)

        Returns:
            Combined PIL Image
        """
        if max_width is None:
            max_width = self.max_width

        # Calculate available width for each image
        available_width = max_width - spacing
        img1_width = available_width // 2
        img2_width = available_width - img1_width

        # Resize images if needed
        if image1.width > img1_width:
            image1 = self.resize(image1, target_width=img1_width)
        if image2.width > img2_width:
            image2 = self.resize(image2, target_width=img2_width)

        # Match heights
        max_height = max(image1.height, image2.height)

        # Create canvas
        total_width = image1.width + spacing + image2.width
        canvas = Image.new("RGB", (total_width, max_height), "white")

        # Paste images
        canvas.paste(image1, (0, 0))
        canvas.paste(image2, (image1.width + spacing, 0))

        return canvas

    def upscale_image_to_max_width(
        self, source: str | Path | Image.Image
    ) -> Image.Image:
        """
        Upscale an image to fit the printer's max width.

        Args:
            source: Image source (path, URL, base64, or PIL Image)

        Returns:
            Upscaled PIL Image
        """
        return self.prepare_for_print(
            source,
            max_height=self.max_width,
            maintain_aspect=True,
            max_width=self.max_width,
            allow_upscale=True,
        )

    def prepare_for_print(
        self,
        source: str | Path | Image.Image,
        max_width: int | None = None,
        max_height: int | None = None,
        rotation: float = 0,
        alignment: Literal["left", "center", "right"] = "left",
        maintain_aspect: bool = True,
        allow_upscale: bool = False,
    ) -> Image.Image:
        """
        Complete preprocessing pipeline for printing.

        Args:
            source: Image source (path, URL, base64, or PIL Image)
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            rotation: Rotation angle in degrees
            alignment: Horizontal alignment
            maintain_aspect: Maintain aspect ratio when resizing
            allow_upscale: Whether images smaller than constraints can be enlarged

        Returns:
            Preprocessed PIL Image ready for printing
        """
        if max_width is None:
            max_width = self.max_width

        # Load image
        image = self.load_image(source)

        # Rotate if needed
        if rotation != 0:
            image = self.rotate(image, rotation)

        # Resize to fit printer constraints (and optionally upscale tiny images).
        if (
            allow_upscale
            or image.width > max_width
            or (max_height is not None and image.height > max_height)
        ):
            image = self.resize(
                image,
                target_width=max_width,
                target_height=max_height,
                maintain_aspect=maintain_aspect,
                allow_upscale=allow_upscale,
            )

        # Add alignment padding
        if alignment != "left":
            image = self.add_horizontal_padding(image, alignment, max_width)

        # Convert to printable format
        image = self.convert_to_printable(image)

        return image

    def save_to_temp(self, image: Image.Image, format: str = "PNG") -> str:
        """
        Save image to temporary file and return path.

        Args:
            image: PIL Image to save
            format: Image format (PNG, BMP, etc.)

        Returns:
            Path to temporary file
        """
        import tempfile

        fd, path = tempfile.mkstemp(suffix=f".{format.lower()}")
        image.save(path, format=format)
        return path
