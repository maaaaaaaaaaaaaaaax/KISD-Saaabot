"""Complex text rendering utilities for thermal printers.

This module renders styled text spans into a PIL image that can be printed
through the existing image pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional, Sequence, Union
import re

from PIL import Image, ImageDraw, ImageFont


FontFamily = Literal['sans', 'sans-b', 'serif', 'monospace']
TextAlign = Literal['left', 'center', 'right']


@dataclass
class ComplexTextSpan:
    """A styled span inside a complex text block."""

    text: str
    font_family: FontFamily = 'sans'
    font_size: int = 28
    bold: bool = False
    italic: bool = False
    underline: bool = False
    invert: bool = False


@dataclass
class ComplexTextBlockStyle:
    """Block-level rendering options for complex text."""

    max_width: Optional[int] = None
    align: TextAlign = 'left'
    line_spacing: float = 1.2
    padding: int = 8
    foreground: str = 'black'
    background: str = 'white'


@dataclass
class _Run:
    text: str
    span: ComplexTextSpan
    font: ImageFont.ImageFont
    width: int


class ComplexTextRenderer:
    """Render complex text spans to PIL images."""

    _token_splitter = re.compile(r'(\n|\s+)')

    def __init__(self, config=None):
        self.config = config

    def render(
        self,
        spans: Sequence[Union[ComplexTextSpan, dict[str, Any]]],
        style: Optional[ComplexTextBlockStyle] = None,
        max_width: Optional[int] = None
    ) -> Image.Image:
        """Render spans into a printable image."""
        if not spans:
            raise ValueError('At least one span is required')

        block_style = self._resolve_block_style(style, max_width)
        normalized_spans = [self._coerce_span(item) for item in spans]

        content_width = max(1, block_style.max_width - block_style.padding * 2)
        lines = self._layout_lines(normalized_spans, content_width)

        if not lines:
            lines = [[]]

        line_heights = [self._line_height(line) for line in lines]
        y_cursor = block_style.padding
        bottom = y_cursor
        for line_height in line_heights:
            bottom = max(bottom, y_cursor + line_height)
            y_cursor += int(round(line_height * block_style.line_spacing))
        total_height = max(1, bottom + block_style.padding)

        image = Image.new('RGB', (block_style.max_width, total_height), block_style.background)
        draw = ImageDraw.Draw(image)

        y = block_style.padding
        for line, line_height in zip(lines, line_heights):
            line_width = sum(run.width for run in line)
            x = self._line_start_x(block_style.align, block_style.padding, content_width, line_width)

            for run in line:
                fg = block_style.foreground
                bg = block_style.background
                if run.span.invert:
                    fg, bg = bg, fg

                if run.span.invert and run.width > 0:
                    draw.rectangle([x, y, x + run.width, y + line_height], fill=bg)

                draw.text((x, y), run.text, font=run.font, fill=fg)

                if run.span.underline and run.width > 0:
                    underline_y = y + line_height - 2
                    draw.line((x, underline_y, x + run.width, underline_y), fill=fg, width=1)

                x += run.width

            y += int(round(line_height * block_style.line_spacing))

        return image

    def _resolve_block_style(
        self,
        style: Optional[ComplexTextBlockStyle],
        max_width: Optional[int]
    ) -> ComplexTextBlockStyle:
        defaults = self.config.get_complex_text_defaults() if self.config else {}

        resolved = style or ComplexTextBlockStyle()
        width_from_config = defaults.get('max_width')
        width = max_width or resolved.max_width or width_from_config

        if width is None:
            width = self.config.max_image_width if self.config else 512

        return ComplexTextBlockStyle(
            max_width=int(width),
            align=resolved.align,
            line_spacing=resolved.line_spacing if resolved.line_spacing > 0 else defaults.get('line_spacing', 1.2),
            padding=max(0, int(resolved.padding)),
            foreground=resolved.foreground or defaults.get('foreground', 'black'),
            background=resolved.background or defaults.get('background', 'white')
        )

    def _coerce_span(self, span: Union[ComplexTextSpan, dict[str, Any]]) -> ComplexTextSpan:
        if isinstance(span, ComplexTextSpan):
            return span

        if isinstance(span, dict):
            text = str(span.get('text', ''))
            return ComplexTextSpan(
                text=text,
                font_family=span.get('font_family', 'sans'),
                font_size=int(span.get('font_size', 28)),
                bold=bool(span.get('bold', False)),
                italic=bool(span.get('italic', False)),
                underline=bool(span.get('underline', False)),
                invert=bool(span.get('invert', False))
            )

        raise TypeError('Each span must be ComplexTextSpan or dict')

    def _layout_lines(self, spans: Sequence[ComplexTextSpan], content_width: int) -> list[list[_Run]]:
        lines: list[list[_Run]] = [[]]
        current_width = 0

        for span in spans:
            font = self._load_font(span)
            tokens = self._tokenize(span.text)

            for token in tokens:
                if token == '\n':
                    lines.append([])
                    current_width = 0
                    continue

                if token and token.isspace() and not lines[-1]:
                    continue

                token_width = self._measure(token, font)

                if current_width + token_width <= content_width:
                    lines[-1].append(_Run(token, span, font, token_width))
                    current_width += token_width
                    continue

                if token.strip() == '':
                    lines.append([])
                    current_width = 0
                    continue

                if lines[-1]:
                    lines.append([])
                    current_width = 0

                for chunk in self._break_token(token, font, content_width):
                    chunk_width = self._measure(chunk, font)
                    if chunk_width > content_width and len(chunk) == 1:
                        # Safety for pathological font metrics
                        chunk_width = content_width

                    if current_width + chunk_width > content_width and lines[-1]:
                        lines.append([])
                        current_width = 0

                    lines[-1].append(_Run(chunk, span, font, chunk_width))
                    current_width += chunk_width

                    if current_width >= content_width:
                        lines.append([])
                        current_width = 0

        if lines and not lines[-1]:
            lines.pop()

        return lines

    def _break_token(self, token: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
        if self._measure(token, font) <= max_width:
            return [token]

        chunks: list[str] = []
        current = ''

        for char in token:
            candidate = current + char
            if current and self._measure(candidate, font) > max_width:
                chunks.append(current)
                current = char
            else:
                current = candidate

        if current:
            chunks.append(current)

        return chunks or [token]

    def _tokenize(self, text: str) -> list[str]:
        if not text:
            return ['']

        parts = self._token_splitter.split(text)
        return [part for part in parts if part != '']

    def _line_height(self, runs: list[_Run]) -> int:
        if not runs:
            return 16
        return max(self._font_line_height(run.font) for run in runs)

    def _font_line_height(self, font: ImageFont.ImageFont) -> int:
        bbox = font.getbbox('Ag')
        return max(1, bbox[3] - bbox[1])

    def _measure(self, text: str, font: ImageFont.ImageFont) -> int:
        if not text:
            return 0
        bbox = font.getbbox(text)
        return max(0, bbox[2] - bbox[0])

    def _line_start_x(self, align: TextAlign, padding: int, content_width: int, line_width: int) -> int:
        if align == 'center':
            return padding + max(0, (content_width - line_width) // 2)
        if align == 'right':
            return padding + max(0, content_width - line_width)
        return padding

    def _load_font(self, span: ComplexTextSpan) -> ImageFont.ImageFont:
        variant = self._variant_name(span.bold, span.italic)
        size = max(8, int(span.font_size))

        font_path = None
        if self.config:
            font_path = self.config.get_complex_text_font_path(span.font_family, variant)
            if font_path is None and variant != 'regular':
                font_path = self.config.get_complex_text_font_path(span.font_family, 'regular')

        if font_path:
            return ImageFont.truetype(str(font_path), size=size)

        # Lightweight fallback chain
        fallback_names = self._fallback_font_names(span.font_family, variant)
        for name in fallback_names:
            try:
                return ImageFont.truetype(name, size=size)
            except OSError:
                continue

        return ImageFont.load_default()

    def _variant_name(self, bold: bool, italic: bool) -> str:
        if bold and italic:
            return 'bold_italic'
        if bold:
            return 'bold'
        if italic:
            return 'italic'
        return 'regular'

    def _fallback_font_names(self, family: FontFamily, variant: str) -> list[str]:
        family_map: dict[FontFamily, list[str]] = {
            'sans': ['DejaVuSans'],
            'sans-b': ['DejaVuSansCondensed', 'DejaVuSans'],
            'serif': ['DejaVuSerif'],
            'monospace': ['DejaVuSansMono']
        }

        suffix_map = {
            'regular': ['.ttf'],
            'bold': ['-Bold.ttf', '.ttf'],
            'italic': ['-Oblique.ttf', '-Italic.ttf', '.ttf'],
            'bold_italic': ['-BoldOblique.ttf', '-BoldItalic.ttf', '.ttf']
        }

        names: list[str] = []
        for base in family_map.get(family, ['DejaVuSans']):
            for suffix in suffix_map.get(variant, ['.ttf']):
                if suffix == '.ttf':
                    names.append(f'{base}.ttf')
                else:
                    names.append(f'{base}{suffix}')
        return names
