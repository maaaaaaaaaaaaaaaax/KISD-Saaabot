"""
Pi-Printer: High-level wrapper for thermal receipt printers.

A well-structured module for working with thermal receipt printers (EPSON TM-T88IV),
built on top of python-escpos. Provides image processing, text formatting, and layout
utilities for creative and exhibition printing.

Example usage:
    from pi_printer import Printer

    with Printer() as p:
        p.print_heading("Hello World", level=1)
        p.print_text("Welcome to thermal printing!")
        p.print_image("logo.png", alignment='center')
        p.cut()
"""

__version__ = "0.1.0"

from .complex_text import ComplexTextBlockStyle, ComplexTextRenderer, ComplexTextSpan
from .config import Config
from .image import ImageProcessor
from .layout import ImageLayout, Layout
from .printer import Printer
from .text import TextFormatter, TextStyle

__all__ = [
    "Printer",
    "Config",
    "ImageProcessor",
    "TextFormatter",
    "TextStyle",
    "Layout",
    "ImageLayout",
    "ComplexTextRenderer",
    "ComplexTextSpan",
    "ComplexTextBlockStyle",
]
