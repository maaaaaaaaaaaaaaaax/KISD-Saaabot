# printer

High-level wrapper for the EPSON TM-T88IV thermal printer, built on [python-escpos](https://python-escpos.readthedocs.io). Connects via USB and exposes text, image, layout, and complex-span rendering through a single `Printer` facade.

## Modules

| File | Responsibility |
|---|---|
| `printer.py` | Main `Printer` facade — connects device, delegates to sub-modules |
| `config.py` | Loads YAML printer profiles; resolves fonts, sizes, USB IDs |
| `image.py` | `ImageProcessor` — load, resize, rotate, dither images for printing |
| `text.py` | `TextFormatter` (chainable) and `TextStyle` dataclass |
| `layout.py` | `Layout` — two-column rows, separators, headers, table rows, text wrapping; `ImageLayout` — horizontal/vertical image composition |
| `complex_text.py` | `ComplexTextRenderer` — renders mixed-style span sequences to a PIL image for high-quality typography |

## Usage

```python
from printer import Printer, ComplexTextSpan, ComplexTextBlockStyle

with Printer() as p:
    # Text
    p.print_heading("RECEIPT", level=1)
    p.print_text("Thank you for your purchase.")
    p.print_two_columns("Total:", "$12.50")
    p.print_separator("=")

    # Image (file path, URL, or base64)
    p.print_image("logo.png", alignment="center")

    # Complex mixed-style spans rendered as an image block
    p.print_complex_text([
        ComplexTextSpan("PRICE ", font_family="monospace", font_size=30, bold=True),
        ComplexTextSpan("30 €", font_family="serif", font_size=34, italic=True),
    ], style=ComplexTextBlockStyle(align="left"))

    p.feed(2)
    p.cut()
```

### TextFormatter (chainable)

```python
formatter = p.format_text("Hello").bold().align("center")
p.print_formatted(formatter)
```

Available methods: `bold()`, `underline()`, `size()`, `align()`, `invert()`, `font()`, `h1()`–`h3()`, `heading(level)`.

### ImageProcessor (standalone)

```python
from printer import ImageProcessor

proc = ImageProcessor(max_width=512)
img = proc.load_image("photo.png")       # also accepts URL or base64
img = proc.resize(img, target_width=400)
img = proc.rotate(img, degrees=90)
```

## Configuration

Profiles live in `profiles/`. The default profile (`tm_t88iv.yaml`) covers print width, DPI, font mappings, text-size presets, image settings, USB IDs, and complex-text font paths.

```python
from printer import Config

cfg = Config("profiles/tm_t88iv.yaml")
print(cfg.max_image_width)   # 512
print(cfg.usb_vendor_id)     # 0x04b8
```

Custom profiles are loaded by passing `config_path` to `Printer(config_path=...)`.

## Image tips

- Target width: 512 px (`magick input.png -resize 512x output.png`)
- High-contrast sources produce the best thermal output
- Floyd-Steinberg dithering is applied automatically
