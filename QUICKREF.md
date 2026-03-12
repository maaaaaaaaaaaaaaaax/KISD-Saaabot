# Pi-Printer Quick Reference

## Project Structure

```
pi-printer/
├── pi_printer/              # Main package
│   ├── __init__.py          # Package exports
│   ├── printer.py           # Main Printer facade class
│   ├── config.py            # Configuration management
│   ├── image.py             # ImageProcessor for image handling
│   ├── text.py              # TextFormatter for text styling
│   ├── layout.py            # Layout utilities
│   └── profiles/
│       └── tm_t88iv.yaml    # TM-T88IV printer profile
├── examples/                # Usage examples
│   ├── basic_usage.py
│   ├── text_formatting.py
│   ├── image_gallery.py
│   └── creative_layout.py
├── main.py                  # Updated test script
└── pyproject.toml          # Package configuration
```

## Quick API Reference

### Basic Printing

```python
from pi_printer import Printer

with Printer() as p:
    p.print_text("Hello World")
    p.cut()
```

### Text Formatting

```python
# Headings
p.print_heading("Title", level=1)  # h1-h3

# Chainable formatter
formatter = p.format_text("Text")
formatter.bold().size(2).align('center')
p.print_formatted(formatter)

# Complex text spans rendered as image
from pi_printer import ComplexTextSpan
spans = [
  ComplexTextSpan("PRICE ", font_family='monospace', bold=True),
  ComplexTextSpan("30€", font_family='serif', italic=True),
]
p.print_complex_text(spans)

# Two columns
p.print_two_columns("Left", "Right")

# Separators
p.print_separator('=')
```

### Image Printing

```python
# Simple
p.print_image("photo.png")

# With options
p.print_image("logo.png", 
              width=400,
              rotation=90,
              alignment='center')

# From URL
p.print_image("https://example.com/image.png")
```

### Layout Helpers

```python
# Feed lines
p.feed(2)

# Cut paper
p.cut()

# QR code
p.qr("https://example.com", size=4, center=True)

# Barcode
p.barcode("123456789012", bc_type='EAN13')
```

## Module Overview

### Printer (Main Interface)
- Entry point for all printing operations
- Context manager support (`with Printer() as p:`)
- Wraps escpos with high-level API
- Auto-connects to TM-T88IV via USB

### Config
- Loads YAML printer profiles
- Defines print dimensions, fonts, text sizes
- Provides typed access to settings
- Default: TM-T88IV profile

### ImageProcessor
- Load images from files, URLs, base64
- Resize, rotate, align images
- Convert formats for thermal printing
- Combine multiple images

### TextFormatter
- Chainable text styling
- Font selection (sans, sans-b)
- Size, alignment, bold
- Heading presets (h1-h3)

### ComplexTextRenderer
- Renders mixed-style spans into images
- Supports serif and monospace font families
- Supports true italic via font files
- Printed via existing image pipeline

### Layout
- Text alignment and wrapping
- Two-column layouts
- Separators and boxes
- Table rows

### ImageLayout
- Image alignment with padding
- Horizontal/vertical image combination
- Size calculations

## Configuration

Default config: `pi_printer/profiles/tm_t88iv.yaml`

```yaml
printer:
  model: "TM-T88IV"
  print_width_dots: 576
  max_image_width_px: 512
  dpi: 203

fonts:
  sans: 'a'
  sans-b: 'b'

text_sizes:
  h1: {width: 3, height: 3}
  h2: {width: 2, height: 2}
  h3: {width: 2, height: 1}

image:
  default_dither: 'floyd_steinberg'
  auto_resize: true
  maintain_aspect_ratio: true
```

## Running Examples

```bash
# Basic usage
sudo .venv/bin/python examples/basic_usage.py

# Text formatting demo
sudo .venv/bin/python examples/text_formatting.py

# Image examples
sudo .venv/bin/python examples/image_gallery.py

# Creative layouts
sudo .venv/bin/python examples/creative_layout.py

# Original test
sudo .venv/bin/python main.py
```

## Tips

1. **Image Preparation**: Resize images to ~512px width for best results
2. **USB Access**: May need `sudo` for USB printer access on Linux/macOS
3. **Error Handling**: Module auto-fixes oversized images and format issues
4. **Dithering**: Floyd-Steinberg default, good for photos/artwork
5. **Font Mapping**: Printer fonts limited - TM-T88IV only has 'sans' (Font A) and 'sans-b' (Font B)

## Common Patterns

### Receipt
```python
with Printer() as p:
    p.print_heading("RECEIPT", level=1)
    p.print_separator('=')
    p.print_two_columns("Item", "Price")
    p.print_separator('-')
    p.print_two_columns("Coffee", "$3.50")
    p.print_two_columns("Total:", "$3.50")
    p.feed(2)
    p.cut()
```

### Exhibition Poster
```python
with Printer() as p:
    p.print_heading("EXHIBITION", level=1)
    p.print_image("artwork.png", alignment='center', width=400)
    p.feed(1)
    p.print_text("Description text...")
    p.qr("https://exhibition.com", size=4, center=True)
    p.cut()
```

### Ticket
```python
with Printer() as p:
    p.print_heading("EVENT TICKET", level=2)
    p.print_two_columns("Date:", "March 15")
    p.print_two_columns("Time:", "14:00")
    p.barcode("123456789012", 'EAN13')
    p.cut()
```
