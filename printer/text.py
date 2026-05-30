"""Text formatting utilities for thermal receipt printers."""

import textwrap
from dataclasses import dataclass
from typing import Literal


@dataclass
class TextStyle:
    """Text style configuration for thermal printer."""

    font: str = "a"  # Font identifier ('a', 'b', 'c')
    bold: bool = False
    underline: int = 0  # 0=off, 1=on, 2=double
    width: int = 1  # Width multiplier (1-8)
    height: int = 1  # Height multiplier (1-8)
    align: Literal["left", "center", "right"] = "left"
    invert: bool = False  # Inverted colors (white on black)

    def copy(self) -> "TextStyle":
        """Create a copy of this style."""
        return TextStyle(
            font=self.font,
            bold=self.bold,
            underline=self.underline,
            width=self.width,
            height=self.height,
            align=self.align,
            invert=self.invert,
        )


class TextFormatter:
    """Chainable text formatter for building styled text."""

    def __init__(self, text: str, config=None):
        """
        Initialize text formatter.

        Args:
            text: Text content to format
            config: Config object for font mappings (optional)
        """
        self.text = text
        self.config = config
        self._style = TextStyle()

    @property
    def style(self) -> TextStyle:
        """Get current text style."""
        return self._style

    def font(self, style: Literal["sans", "sans-b"]) -> "TextFormatter":
        """
        Set font style.

        Args:
            style: Font style ('sans', 'sans-b')

        Returns:
            Self for chaining
        """
        if self.config:
            self._style.font = self.config.get_font(style)
        else:
            # Default mapping (TM-T88IV only has fonts 'a' and 'b')
            font_map = {"sans": "a", "sans-b": "b"}
            self._style.font = font_map.get(style, "a")
        return self

    def bold(self, enabled: bool = True) -> "TextFormatter":
        """
        Enable/disable bold text.

        Args:
            enabled: Whether to enable bold

        Returns:
            Self for chaining
        """
        self._style.bold = enabled
        return self

    def underline(self, mode: int = 1) -> "TextFormatter":
        """
        Set underline mode.

        Args:
            mode: Underline mode (0=off, 1=single, 2=double)

        Returns:
            Self for chaining
        """
        self._style.underline = mode
        return self

    def size(self, width: int, height: int | None = None) -> "TextFormatter":
        """
        Set text size multipliers.

        Args:
            width: Width multiplier (1-8)
            height: Height multiplier (1-8), defaults to width if not specified

        Returns:
            Self for chaining
        """
        self._style.width = max(1, min(8, width))
        self._style.height = max(1, min(8, height if height is not None else width))
        return self

    def align(self, alignment: Literal["left", "center", "right"]) -> "TextFormatter":
        """
        Set text alignment.

        Args:
            alignment: Alignment ('left', 'center', 'right')

        Returns:
            Self for chaining
        """
        self._style.align = alignment
        return self

    def invert(self, enabled: bool = True) -> "TextFormatter":
        """
        Enable/disable inverted colors (white on black).

        Args:
            enabled: Whether to invert colors

        Returns:
            Self for chaining
        """
        self._style.invert = enabled
        return self

    def heading(self, level: int) -> "TextFormatter":
        """
        Apply heading style (h1-h3).

        Args:
            level: Heading level (1-3)

        Returns:
            Self for chaining
        """
        if self.config:
            size = self.config.get_text_size(f"h{level}")
        else:
            # Default heading sizes
            sizes = {
                1: {"width": 3, "height": 3},
                2: {"width": 2, "height": 2},
                3: {"width": 2, "height": 1},
            }
            size = sizes.get(level, {"width": 1, "height": 1})

        self._style.width = size["width"]
        self._style.height = size["height"]
        self._style.bold = True
        return self

    def h1(self) -> "TextFormatter":
        """Apply h1 heading style."""
        return self.heading(1)

    def h2(self) -> "TextFormatter":
        """Apply h2 heading style."""
        return self.heading(2)

    def h3(self) -> "TextFormatter":
        """Apply h3 heading style."""
        return self.heading(3)

    def normal(self) -> "TextFormatter":
        """Reset to normal text style."""
        self._style = TextStyle()
        return self


def wrap_text(text: str, max_width: int) -> list[str]:
    """
    Wrap text to fit within specified character width.

    Args:
        text: Text to wrap
        max_width: Maximum characters per line

    Returns:
        List of wrapped lines
    """
    if max_width <= 0:
        return [text]

    # Handle multiple paragraphs
    paragraphs = text.split("\n")
    wrapped_lines = []

    for para in paragraphs:
        if not para.strip():
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(textwrap.wrap(para, width=max_width))

    return wrapped_lines


def pad_line(
    text: str, width: int, align: Literal["left", "center", "right"] = "left"
) -> str:
    """
    Pad text to specified width with alignment.

    Args:
        text: Text to pad
        width: Total width in characters
        align: Alignment ('left', 'center', 'right')

    Returns:
        Padded text
    """
    text_len = len(text)
    if text_len >= width:
        return text

    padding = width - text_len

    if align == "center":
        left_pad = padding // 2
        right_pad = padding - left_pad
        return " " * left_pad + text + " " * right_pad
    elif align == "right":
        return " " * padding + text
    else:  # left
        return text + " " * padding


def create_two_column_text(
    left_text: str, right_text: str, total_width: int, separator: str = " "
) -> str:
    """
    Create two-column text.

    Args:
        left_text: Left column text.
        right_text: Right column text.
        total_width: Total width in characters.
        separator: Separator between columns.

    Returns:
        Formatted text. May include newlines when content wraps.
    """
    if total_width <= 0:
        return ""

    separator_len = len(separator)
    if separator_len >= total_width:
        return left_text

    # Reserve dynamic width for right column while keeping at least one char for left
    max_right_width = max(0, total_width - separator_len - 1)
    right_col_width = min(len(right_text), max_right_width)
    left_col_width = total_width - separator_len - right_col_width

    # If right text does not fit into its column width, it wraps to additional rows.
    left_lines = wrap_text(left_text, left_col_width) if left_col_width > 0 else [""]
    right_lines = (
        wrap_text(right_text, right_col_width) if right_col_width > 0 else [""]
    )

    line_count = max(len(left_lines), len(right_lines))
    lines = []

    for index in range(line_count):
        left_part = left_lines[index] if index < len(left_lines) else ""
        right_part = right_lines[index] if index < len(right_lines) else ""

        if left_col_width > 0:
            left_part = left_part.ljust(left_col_width)

        if right_col_width > 0:
            right_part = right_part.rjust(right_col_width)
            lines.append(f"{left_part}{separator}{right_part}")
        else:
            lines.append(left_part)

    return "\n".join(lines)


def create_two_column_line(
    left_text: str, right_text: str, total_width: int, separator: str = " "
) -> str:
    """Backward-compatible alias for create_two_column_text."""
    return create_two_column_text(left_text, right_text, total_width, separator)


def create_separator(width: int, char: str = "-") -> str:
    """
    Create a separator line.

    Args:
        width: Width in characters
        char: Character to use for separator

    Returns:
        Separator line
    """
    return char * width
