"""
Text formatting example for pi-printer module.

Demonstrates native ESC/POS text and complex span-based text as image blocks.
"""

from printer import Printer, ComplexTextSpan, ComplexTextBlockStyle

def main():
    with Printer() as p:
        p.initialize()
        # Complex text block rendered as image (mixed styles)
        p.print_text("Complex Text Block", style='h3')
        complex_spans = [
            ComplexTextSpan("PRICE AND ", font_family='monospace', font_size=30, bold=True),
            ComplexTextSpan("30€", font_family='serif', font_size=34, italic=True),
            ComplexTextSpan(", Brown\n", font_family='sans', font_size=26),
            ComplexTextSpan(", Super small\n", font_family='sans', font_size=12),
            ComplexTextSpan(", Some serif text, this is some serif text.\n", font_family='serif', font_size=22),
            ComplexTextSpan(", INTERESTING\n", font_family='sans', bold=True, italic=True, underline=True, invert=True, font_size=30),
            ComplexTextSpan("FURTHER DETAILS", font_family='sans-b', font_size=24),
        ]
        p.print_complex_text(
            spans=complex_spans,
            style=ComplexTextBlockStyle(align='left', padding=10, line_spacing=1.15)
        )
        p.print_complex_text(
            spans=[ComplexTextSpan("This is a long text that should wrap around to the next line if it exceeds the printer's width. It demonstrates automatic text wrapping in complex text blocks.", font_family='sans', font_size=20)],
            style=ComplexTextBlockStyle(align='center', padding=20, line_spacing=1.5)
        )
        p.print_complex_text(
            spans=[ComplexTextSpan("This is a long text that should wrap around to the next line if it exceeds the printer's width. It demonstrates automatic text wrapping in complex text blocks.", font_family='sans', font_size=20)],
            style=ComplexTextBlockStyle(align='left', padding=20, line_spacing=1.5)
        )
        p.print_complex_text(
            spans=[ComplexTextSpan("This is a long text that should wrap around to the next line if it exceeds the printer's width. It demonstrates automatic text wrapping in complex text blocks.", font_family='sans', font_size=20)],
            style=ComplexTextBlockStyle(align='right', padding=20, line_spacing=1.5)
        )
        p.feed(2)
        p.cut()

if __name__ == "__main__":
    main()
