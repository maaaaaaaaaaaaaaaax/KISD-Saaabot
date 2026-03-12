"""Layout utilities for composing text and images on thermal receipts."""

from typing import Literal, Optional, Union, List
from PIL import Image
from .text import create_two_column_text, create_separator, pad_line, wrap_text


class Layout:
    """Layout helper for composing receipt content."""

    def __init__(self, config=None):
        """
        Initialize layout manager.

        Args:
            config: Config object for printer specifications
        """
        self.config = config

        # Default to 48 chars per line (Font A at 1x)
        self._chars_per_line = 48
        self._max_image_width = 531

        if config:
            self._chars_per_line = config.chars_per_line.get("a", 48)
            self._max_image_width = config.max_image_width

    def set_chars_per_line(self, chars: int):
        """Set the number of characters per line for text operations."""
        self._chars_per_line = chars

    def align_text(
        self,
        text: str,
        alignment: Literal["left", "center", "right"] = "left",
        width: Optional[int] = None,
    ) -> str:
        """
        Align text within specified width.

        Args:
            text: Text to align
            alignment: Alignment ('left', 'center', 'right')
            width: Width in characters (default: chars_per_line)

        Returns:
            Aligned text
        """
        if width is None:
            width = self._chars_per_line

        return pad_line(text, width, alignment)

    def two_column_text(
        self,
        left_text: str,
        right_text: str,
        separator: str = " ",
        width: Optional[int] = None,
    ) -> str:
        """
        Create two-column text.

        Args:
            left_text: Left column text.
            right_text: Right column text.
            separator: Separator between columns.
            width: Total width in characters.

        Returns:
            Formatted text. May include newlines when content wraps.
        """
        if width is None:
            width = self._chars_per_line

        return create_two_column_text(left_text, right_text, width, separator)

    def wrap_text(self, text: str, width: Optional[int] = None) -> List[str]:
        """
        Wrap text to fit line width.

        Args:
            text: Text to wrap
            width: Maximum width in characters (default: chars_per_line)

        Returns:
            List of wrapped lines
        """
        if width is None:
            width = self._chars_per_line

        return wrap_text(text, width)

    def separator(self, char: str = "-", width: Optional[int] = None) -> str:
        """
        Create a separator line.

        Args:
            char: Character to use for separator
            width: Width in characters (default: chars_per_line)

        Returns:
            Separator line
        """
        if width is None:
            width = self._chars_per_line

        return create_separator(width, char)

    def header(
        self, text: str, separator_char: str = "=", width: Optional[int] = None
    ) -> str:
        """
        Create a centered header with separator.

        Args:
            text: Header text
            separator_char: Character for separator line
            width: Width in characters (default: chars_per_line)

        Returns:
            Formatted header with separator
        """
        if width is None:
            width = self._chars_per_line

        centered = self.align_text(text, "center", width)
        sep = self.separator(separator_char, width)
        return f"{centered}\n{sep}"

    def footer(
        self, text: str, separator_char: str = "=", width: Optional[int] = None
    ) -> str:
        """
        Create a centered footer with separator.

        Args:
            text: Footer text
            separator_char: Character for separator line
            width: Width in characters (default: chars_per_line)

        Returns:
            Formatted footer with separator
        """
        if width is None:
            width = self._chars_per_line

        sep = self.separator(separator_char, width)
        centered = self.align_text(text, "center", width)
        return f"{sep}\n{centered}"

    def spacer(self, lines: int = 1) -> str:
        """
        Create vertical spacing.

        Args:
            lines: Number of blank lines

        Returns:
            Newline characters
        """
        return "\n" * lines

    def table_row(
        self,
        columns: List[str],
        widths: Optional[List[int]] = None,
        separator: str = " ",
    ) -> str:
        """
        Create a table row with multiple columns.

        Args:
            columns: List of column texts
            widths: List of column widths (auto-calculated if None)
            separator: Separator between columns

        Returns:
            Formatted table row
        """
        if not columns:
            return ""

        total_width = self._chars_per_line
        sep_width = len(separator) * (len(columns) - 1)
        available_width = total_width - sep_width

        if widths is None:
            # Equal width columns
            col_width = available_width // len(columns)
            widths = [col_width] * len(columns)

        # Truncate and pad columns
        formatted_cols = []
        for text, width in zip(columns, widths):
            if len(text) > width:
                text = text[: max(0, width - 3)] + "..."
            formatted_cols.append(text.ljust(width))

        return separator.join(formatted_cols)

    def box(
        self,
        text: str,
        top_char: str = "-",
        side_char: str = "|",
        width: Optional[int] = None,
    ) -> str:
        """
        Create a text box with border.

        Args:
            text: Text to box
            top_char: Character for top/bottom border
            side_char: Character for side borders
            width: Width in characters (default: chars_per_line)

        Returns:
            Boxed text
        """
        if width is None:
            width = self._chars_per_line

        inner_width = width - 4  # Account for borders and padding
        lines = self.wrap_text(text, inner_width)

        border = top_char * width
        boxed_lines = [border]

        for line in lines:
            padded = line.ljust(inner_width)
            boxed_lines.append(f"{side_char} {padded} {side_char}")

        boxed_lines.append(border)
        return "\n".join(boxed_lines)


class ImageLayout:
    """Layout utilities specifically for images."""

    def __init__(self, max_width: int = 531):
        """
        Initialize image layout manager.

        Args:
            max_width: Maximum image width in pixels
        """
        self.max_width = max_width

    def align_image(
        self, image: Image.Image, alignment: Literal["left", "center", "right"] = "left"
    ) -> Image.Image:
        """
        Align image by adding horizontal padding.

        Args:
            image: PIL Image to align
            alignment: Alignment ('left', 'center', 'right')

        Returns:
            Padded PIL Image
        """
        if image.width >= self.max_width or alignment == "left":
            return image

        # Create white canvas
        canvas = Image.new("RGB", (self.max_width, image.height), "white")

        # Calculate x position
        if alignment == "center":
            x = (self.max_width - image.width) // 2
        else:  # right
            x = self.max_width - image.width

        canvas.paste(image, (x, 0))
        return canvas

    def combine_images_horizontal(
        self, image1: Image.Image, image2: Image.Image, spacing: int = 10
    ) -> Image.Image:
        """
        Combine two images side by side.

        Args:
            image1: First image (left)
            image2: Second image (right)
            spacing: Spacing between images in pixels

        Returns:
            Combined PIL Image
        """
        # Calculate dimensions
        total_width = image1.width + spacing + image2.width
        max_height = max(image1.height, image2.height)

        # Create canvas
        canvas = Image.new("RGB", (total_width, max_height), "white")

        # Paste images (vertically centered if heights differ)
        y1 = (max_height - image1.height) // 2
        y2 = (max_height - image2.height) // 2

        canvas.paste(image1, (0, y1))
        canvas.paste(image2, (image1.width + spacing, y2))

        return canvas

    def combine_images_vertical(
        self,
        images: List[Image.Image],
        spacing: int = 10,
        alignment: Literal["left", "center", "right"] = "center",
    ) -> Image.Image:
        """
        Stack images vertically.

        Args:
            images: List of PIL Images to stack
            spacing: Vertical spacing between images in pixels
            alignment: Horizontal alignment of images

        Returns:
            Combined PIL Image
        """
        if not images:
            raise ValueError("At least one image required")

        # Calculate dimensions
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + spacing * (len(images) - 1)

        # Create canvas
        canvas = Image.new("RGB", (max_width, total_height), "white")

        # Paste images
        y_offset = 0
        for img in images:
            # Calculate x position based on alignment
            if alignment == "center":
                x = (max_width - img.width) // 2
            elif alignment == "right":
                x = max_width - img.width
            else:  # left
                x = 0

            canvas.paste(img, (x, y_offset))
            y_offset += img.height + spacing

        return canvas
