"""High-level printer facade for thermal receipt printers."""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from escpos import printer
from PIL import Image

from .complex_text import ComplexTextBlockStyle, ComplexTextRenderer, ComplexTextSpan
from .config import Config
from .image import ImageProcessor
from .layout import ImageLayout, Layout
from .text import TextFormatter, TextStyle


class Printer:
    """
    High-level wrapper for thermal receipt printer with image, text, and layout support.

    Example:
        with Printer() as p:
            p.print_heading("Receipt", level=1)
            p.print_text("Thank you for your purchase!")
            p.print_image("logo.png", alignment='center')
            p.cut()
    """

    def __init__(
        self,
        config_path: str | None = None,
        vendor_id: int | None = None,
        product_id: int | None = None,
        profile: str | None = None,
    ):
        """
        Initialize printer with configuration.

        Args:
            config_path: Path to YAML config file (default: TM-T88IV profile)
            vendor_id: USB vendor ID (default: from config)
            product_id: USB product ID (default: from config)
            profile: escpos profile name (default: from config)
        """
        # Load configuration
        self.config = Config(config_path)

        # Setup USB parameters
        self._vendor_id = vendor_id or self.config.usb_vendor_id
        self._product_id = product_id or self.config.usb_product_id
        self._profile = profile or self.config.usb_profile

        # Initialize modules
        self.image_processor = ImageProcessor(max_width=self.config.max_image_width)
        self.complex_text_renderer = ComplexTextRenderer(config=self.config)
        self.layout = Layout(config=self.config)
        self.image_layout = ImageLayout(max_width=self.config.max_image_width)

        # Printer instance (created on connect)
        self._printer = None
        self._current_font = "a"
        self._current_width_multiplier = 1

    def connect(self):
        """Connect to printer via USB."""
        if self._printer is None:
            self._printer = printer.Usb(
                self._vendor_id, self._product_id, profile=self._profile
            )

    def disconnect(self):
        """Disconnect from printer."""
        if self._printer:
            try:
                self._printer.close()
            except Exception as e:
                print(f"Warning: Failed to close printer connection: {e}")
                pass
            self._printer = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False

    @property
    def device(self):
        """Get underlying escpos printer device."""
        if self._printer is None:
            self.connect()
        return self._printer

    # Text output methods

    def text(self, content: str, style: TextStyle | str | None = None) -> "Printer":
        """
        Print text with optional formatting.

        Args:
            content: Text to print
            style: TextStyle object or preset name ('h1', 'h2', 'h3', 'normal')

        Returns:
            Self for chaining
        """
        # Parse style
        if isinstance(style, str):
            formatter = TextFormatter(content, self.config)
            if style in ["h1", "h2", "h3"]:
                formatter.heading(int(style[1]))
            text_style = formatter.style
        elif isinstance(style, TextStyle):
            text_style = style
        else:
            text_style = TextStyle()

        # Apply style to printer
        self._apply_text_style(text_style)

        # Print text
        self.device.text(content)

        # Always reset to normal after printing to prevent style bleed
        self._reset_text_style()

        return self

    def print_text(
        self, content: str, style: TextStyle | str | None = None
    ) -> "Printer":
        """
        Print text with newline.

        Args:
            content: Text to print
            style: TextStyle object or preset name

        Returns:
            Self for chaining
        """
        return self.text(content + "\n", style)

    def print_heading(self, content: str, level: int = 1) -> "Printer":
        """
        Print heading text.

        Args:
            content: Heading text
            level: Heading level (1-4)

        Returns:
            Self for chaining
        """
        return self.print_text(content, f"h{level}")

    def format_text(self, content: str) -> TextFormatter:
        """
        Create a text formatter for chainable formatting.

        Args:
            content: Text to format

        Returns:
            TextFormatter instance
        """
        return TextFormatter(content, self.config)

    def print_formatted(self, formatter: TextFormatter) -> "Printer":
        """
        Print text using a TextFormatter.

        Args:
            formatter: Configured TextFormatter

        Returns:
            Self for chaining
        """
        return self.text(formatter.text, formatter.style)

    def print_complex_text(
        self,
        spans: Sequence[ComplexTextSpan | dict],
        style: ComplexTextBlockStyle | None = None,
        width: int | None = None,
        alignment: Literal["left", "center", "right"] = "left",
        high_density: bool | None = None,
    ) -> "Printer":
        """
        Render styled span text as an image block and print it.

        Args:
            spans: Sequence of ComplexTextSpan or span dictionaries
            style: Optional block style options
            width: Maximum rendered width in pixels (default: from config)
            alignment: Block text alignment inside rendered width
            high_density: High-density image mode (default: from config)

        Returns:
            Self for chaining
        """
        block_style = style or ComplexTextBlockStyle()
        block_style.align = alignment

        image = self.complex_text_renderer.render(
            spans=spans, style=block_style, max_width=width
        )

        return self.print_image(
            source=image, width=width, alignment="left", high_density=high_density
        )

    def _apply_text_style(self, style: TextStyle):
        """Apply text style to printer."""
        # Check if custom size is needed
        custom_size = style.width != 1 or style.height != 1

        self.device.set(
            align=style.align,
            font=style.font,
            bold=style.bold,
            underline=style.underline,
            custom_size=custom_size,
            width=style.width,
            height=style.height,
            invert=style.invert,
        )
        self._current_font = style.font
        self._current_width_multiplier = style.width

    def _reset_text_style(self):
        """Reset to default text style."""
        self.device.set(
            align="left",
            font="a",
            bold=False,
            underline=0,
            custom_size=True,
            width=1,
            height=1,
            invert=False,
        )
        self._current_font = "a"
        self._current_width_multiplier = 1

    # Image output methods
    def print_image(
        self,
        source: str | Path | Image.Image,
        width: int | None = None,
        full_width: bool = False,
        rotation: float = 0,
        alignment: Literal["left", "center", "right"] = "left",
        high_density: bool | None = None,
    ) -> "Printer":
        """
        Print image with preprocessing.

        Args:
            source: Image source (path, URL, base64, or PIL Image)
            width: Target width in pixels (default: max width from config)
            full_width: Force image to fit a max-size square using printer max width,
                upscaling tiny images when needed
            rotation: Rotation angle in degrees
            alignment: Horizontal alignment
            high_density: Use high-density mode for both vertical
                and horizontal (default: from config)

        Returns:
            Self for chaining
        """
        force_square_fit = full_width
        if full_width:
            width = self.config.max_image_width
        elif width is None:
            width = self.config.max_image_width

        if high_density is None:
            high_density = self.config.high_density

        try:
            # Preprocess image
            image = self.image_processor.prepare_for_print(
                source,
                max_width=width,
                max_height=width if force_square_fit else None,
                rotation=rotation,
                alignment=alignment,
                maintain_aspect=self.config.maintain_aspect_ratio,
                allow_upscale=force_square_fit,
            )

            # Save to temp file and print
            temp_path = self.image_processor.save_to_temp(image)
            self.device.image(
                temp_path,
                high_density_vertical=high_density,
                high_density_horizontal=high_density,
                center=(alignment == "center"),
            )

            # Clean up temp file
            import os

            os.unlink(temp_path)

        except Exception as e:
            # Auto-fix: if image fails, try with smaller size
            if self.config.auto_resize and width > 100:
                print(
                    f"Warning: Image processing failed, retrying with reduced size: {e}"
                )
                return self.print_image(
                    source,
                    width=width // 2,
                    full_width=False,
                    rotation=rotation,
                    alignment=alignment,
                    high_density=high_density,
                )
            else:
                raise

        return self

    # Layout methods

    def print_separator(
        self, char: str = "-", rows: int = 2, width: int | None = None
    ) -> "Printer":
        """
        Print a separator line.

        Args:
            char: Character for separator
            rows: Number of rows to print (default: 1)
            width: Width in characters (default: from config)

        Returns:
            Self for chaining
        """
        if width is None:
            width = self.config.get_chars_per_line(
                self._current_font, self._current_width_multiplier
            )

        sep = self.layout.separator(char, width)
        for _ in range(rows):
            self.print_text(sep)
        return self

    def print_two_columns(
        self, left: str, right: str, separator: str = " "
    ) -> "Printer":
        """
        Print text in two columns.

        Args:
            left: Left column text
            right: Right column text
            separator: Separator between columns (default: single space)

        Returns:
            Self for chaining
        """
        # Use our layout module for two-column formatting
        width = self.config.get_chars_per_line(
            self._current_font, self._current_width_multiplier
        )
        line = self.layout.two_column_text(left, right, separator, width)
        self.device.text(line + "\n")
        return self

    def feed(self, lines: int = 1) -> "Printer":
        """
        Feed paper (blank lines).

        Args:
            lines: Number of lines to feed

        Returns:
            Self for chaining
        """
        self.device.ln(lines)
        return self

    def cut(self, mode: str = "FULL") -> "Printer":
        """
        Cut paper.

        Args:
            mode: Cut mode ('FULL' or 'PART')

        Returns:
            Self for chaining
        """
        self.device.cut(mode=mode)
        return self

    # Direct escpos methods

    def barcode(
        self,
        code: str,
        bc_type: str = "EAN13",
        height: int = 64,
        width: int = 3,
        pos: str = "BELOW",
        font: str = "A",
    ) -> "Printer":
        """
        Print barcode.

        Args:
            code: Barcode data
            bc_type: Barcode type (EAN13, CODE39, CODE128, etc.)
            height: Barcode height in dots
            width: Bar width (2-6)
            pos: Text position (ABOVE, BELOW, BOTH, OFF)
            font: Text font (A or B)

        Returns:
            Self for chaining
        """
        self.device.barcode(
            code, bc_type, height=height, width=width, pos=pos, font=font
        )
        return self

    def qr(self, content: str, size: int = 3, center: bool = True) -> "Printer":
        """
        Print QR code.

        Args:
            content: QR code content
            size: QR code size (1-16)
            center: Center the QR code

        Returns:
            Self for chaining
        """
        self.device.qr(content, size=size, center=center)
        return self

    def initialize(self) -> "Printer":
        """
        Initialize/reset printer.

        Returns:
            Self for chaining
        """
        self.device.hw("INIT")
        return self
