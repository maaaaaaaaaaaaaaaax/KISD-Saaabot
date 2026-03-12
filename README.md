# pi-printer

A high-level Python wrapper for thermal receipt printers (EPSON TM-T88IV) built on top of [python-escpos](https://python-escpos.readthedocs.io). Provides intuitive APIs for image processing, text formatting, and layout composition—perfect for creative printing, exhibition installations, and artistic projects.

## Features

- **Image Processing**: Load images from local files, URLs, or base64 strings with automatic resizing, rotation, and alignment
- **Text Formatting**: Semantic heading styles (h1-h3), bold, multiple fonts, and flexible sizing
- **Complex Text Blocks**: Render mixed-style span lists (serif, monospace, true italic) as image blocks
- **Layout Utilities**: Two-column layouts, separators, alignment, and complex compositions
- **Auto-Fix**: Graceful error handling with automatic image resizing and format conversion
- **Configuration-Driven**: YAML-based printer profiles for easy customization
- **Chainable API**: Fluent interface for building complex print jobs

## Installation

### Raspberry Pi Setup

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install libcups2-dev libusb-1.0-0-dev

# Clone repository
git clone https://github.com/mschmalenbach/pi-printer.git
cd pi-printer

# Install with uv
uv sync

# Run examples (may need sudo for USB access)
sudo .venv/bin/python examples/basic_usage.py
```

### Manual Installation

```bash
pip install python-escpos[all] pillow pyyaml requests
```

## Quick Start

```python
from pi_printer import Printer

# Simple printing
with Printer() as p:
    p.print_heading("Hello World", level=1)
    p.print_text("Welcome to thermal printing!")
    p.print_image("logo.png", alignment='center')
    p.cut()
```

## Usage Examples

### Text Formatting

```python
from pi_printer import Printer

with Printer() as p:
    # Headings
    p.print_heading("Main Title", level=1)
    p.print_heading("Subtitle", level=2)
    
    # Styled text with chainable formatter
    formatter = p.format_text("Bold and centered").bold().align('center')
    p.print_formatted(formatter)
    
    # Two-column layout
    p.print_two_columns("Item:", "Price")
    p.print_two_columns("Coffee", "$3.50")
    
    # Separator lines
    p.print_separator('=')
    
    p.cut()
```

### Image Processing

```python
from pi_printer import Printer

with Printer() as p:
    # Local image with alignment
    p.print_image("photo.png", alignment='center')
    
    # Image from URL
    p.print_image("https://example.com/image.png")
    
    # Rotated and resized
    p.print_image("logo.png", rotation=90, width=300)
    
    # Advanced: Side-by-side images
    from pi_printer import ImageProcessor
    processor = ImageProcessor()
    img1 = processor.load_image("image1.png")
    img2 = processor.load_image("image2.png")
    combined = processor.combine_horizontal(img1, img2, spacing=10)
    p.print_image(combined)
    
    p.cut()
```

### Creative Layouts

```python
from pi_printer import Printer

with Printer() as p:
    # Exhibition poster
    p.print_heading("EXHIBITION", level=1)
    p.print_text("Art & Technology").align('center')
    p.print_separator('=')
    p.feed(2)
    
    p.print_image("artwork.png", alignment='center', width=400)
    p.feed(2)
    
    p.print_text("About", style='h2')
    p.print_text("Explore the intersection of art and computation...")
    p.feed(1)
    
    # QR code for more info
    p.qr("https://example.com/exhibition", size=4, center=True)
    
    p.cut()
```

## Configuration

The module uses YAML configuration files to define printer profiles. The default profile for TM-T88IV is included:

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
```

Custom profiles can be loaded:

```python
config = Config('path/to/custom_profile.yaml')
printer = Printer(config_path='path/to/custom_profile.yaml')
```

## API Reference

### Printer Class

Main interface for printing operations.

**Text Methods:**
- `print_text(content, style)` - Print text with optional style
- `print_heading(content, level)` - Print heading (h1-h3)
- `format_text(content)` - Create chainable TextFormatter
- `print_complex_text(spans, style)` - Render styled spans as image and print
- `print_two_columns(left, right)` - Two-column layout

**Image Methods:**
- `print_image(source, width, rotation, alignment)` - Print image with preprocessing
- `print_separator(char, width)` - Print separator line

**Layout Methods:**
- `feed(lines)` - Feed blank lines
- `cut(mode)` - Cut paper

**Barcode/QR:**
- `barcode(code, bc_type, ...)` - Print barcode
- `qr(content, size, center)` - Print QR code

### TextFormatter Class

Chainable text formatting builder.

```python
formatter = TextFormatter("Hello")
formatter.bold().size(2).align('center')
```

**Methods:** `bold()`, `underline()`, `size()`, `align()`, `invert()`, `font()`, `h1()`, `h2()`, `h3()`

### Complex Text (Image Rendered)

```python
from pi_printer import Printer, ComplexTextSpan, ComplexTextBlockStyle

with Printer() as p:
  spans = [
    ComplexTextSpan("PRICE ", font_family='monospace', font_size=30, bold=True),
    ComplexTextSpan("30€", font_family='serif', font_size=34, italic=True),
    ComplexTextSpan("\nFURTHER DETAILS", font_family='sans-b', font_size=24),
  ]
  p.print_complex_text(spans, style=ComplexTextBlockStyle(align='left'))
```

### ImageProcessor Class

Image loading and preprocessing utilities.

```python
processor = ImageProcessor(max_width=531)
image = processor.load_image("photo.png")  # or URL or base64
image = processor.resize(image, target_width=400)
image = processor.rotate(image, degrees=90)
```

## Hardware

Developed and tested with:
- **Printer:** EPSON TM-T88IV
- **Connection:** USB (VID: 0x04b8, PID: 0x0202)
- **Paper:** 80mm thermal receipt paper
- **Print Width:** 576 dots (203 DPI)

## Examples

See the `examples/` directory for complete demonstrations:
- `basic_usage.py` - Simple text and image printing
- `text_formatting.py` - Advanced text formatting
- `image_gallery.py` - Image loading and manipulation
- `creative_layout.py` - Exhibition posters, tickets, and zines

## Image Tips

For best results:
- Convert images to 531px width: `magick image.png -resize 531x image_resized.png`
- Use high-contrast images (thermal printers are monochrome)
- PNG or JPG format recommended
- Automatic dithering is applied (Floyd-Steinberg by default)

## License

MIT License - see LICENSE file for details

## Credits

Built for KISD MA Thesis project exploring creative applications of thermal printing in exhibition contexts.

Based on [python-escpos](https://github.com/python-escpos/python-escpos) by the python-escpos developers.
