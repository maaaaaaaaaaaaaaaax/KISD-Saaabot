"""
Creative layout example for pi-printer module.

Demonstrates complex layouts combining text and images for exhibition/creative printing.
"""

from printer import Printer


def print_poster(p):
    """Print a creative poster layout."""
    p.initialize()

    # Header with large title
    p.feed(1)
    formatter = p.format_text("EXHIBITION").h1().align("center")
    p.print_formatted(formatter)
    p.feed(1)

    formatter = p.format_text("Art & Technology").h3().align("center")
    p.print_formatted(formatter)
    p.feed(1)

    p.print_separator("=")
    p.feed(2)

    # Feature image
    try:
        p.print_image(
            "examples/printer/assets/gamba.png", alignment="center", width=400
        )
        p.feed(2)
    except Exception:
        p.print_text("[Image placeholder]", style="h3")
        p.feed(2)

    # Description
    formatter = p.format_text("About the Exhibition").h2()
    p.print_formatted(formatter)
    p.feed(1)

    description = (
        "Experience the intersection of art and technology. "
        "This exhibition explores creative expression through "
        "computational media and interactive installations."
    )
    p.print_text(description)
    p.feed(2)

    # Info section
    p.print_separator("-")
    p.print_two_columns("Date:", "March 15-20, 2026")
    p.print_two_columns("Time:", "10:00 - 18:00")
    p.print_two_columns("Location:", "KISD Gallery")
    p.print_separator("-")
    p.feed(2)

    # QR code for more info
    p.print_text("Scan for more info:", style="h3")
    p.qr("https://example.com/exhibition", size=4, center=True)
    p.feed(1)

    p.cut()


def print_ticket(p):
    """Print a ticket layout."""
    p.initialize()

    # Ticket header
    formatter = p.format_text("TICKET").h2().align("center").invert()
    p.print_formatted(formatter)
    p.feed(1)

    # Event details
    formatter = p.format_text("Art Exhibition 2026").h3().align("center")
    p.print_formatted(formatter)
    p.feed(1)

    p.print_separator("=")
    p.feed(1)

    # Ticket info
    p.print_two_columns("Ticket #:", "A-12345")
    p.print_two_columns("Type:", "General Admission")
    p.print_two_columns("Date:", "March 15, 2026")
    p.print_two_columns("Time:", "14:00")
    p.feed(1)

    # Small image/logo
    try:
        p.print_image("examples/printer/assets/fly.png", alignment="center", width=200)
    except Exception:
        pass
    p.feed(1)

    # Barcode
    p.barcode("123456789012", bc_type="EAN13", height=50, pos="BELOW")
    p.feed(1)

    p.print_separator("-")
    p.print_text("Present at entrance", style="h3")
    p.feed(2)

    p.cut()


def print_zine_page(p):
    """Print a zine-style page layout."""
    p.initialize()

    # Zine header with decorative elements
    p.print_separator("*")
    formatter = p.format_text("DIGITAL ZINE").h1().align("center")
    p.print_formatted(formatter)
    formatter = p.format_text("Issue #1 - Spring 2026").align("center")
    p.print_formatted(formatter)
    p.print_separator("*")
    p.feed(2)

    # Article title
    formatter = p.format_text("The Future of Print").h2().bold()
    p.print_formatted(formatter)
    p.feed(1)

    # Article body
    article = (
        "In an increasingly digital world, thermal printing "
        "offers a unique tactile experience. Each print is a "
        "physical artifact, a moment captured on thermal paper."
    )
    p.print_text(article)
    p.feed(2)

    # Pull quote (centered, bold)
    p.print_separator("~")
    formatter = p.format_text('"Print is not dead"').h3().align("center")
    p.print_formatted(formatter)
    p.print_separator("~")
    p.feed(2)

    # Image
    try:
        p.print_image(
            "examples/printer/assets/gamba.png", alignment="center", width=300
        )
    except Exception:
        pass
    p.feed(2)

    # Tiny-image upscale demo (forces image to fill printer max range)
    p.print_separator("-")
    p.print_text("Upscaled Trigger Sample", style="h3")
    try:
        p.print_image("examples/printer/assets/example-triggered.png", full_width=True)
    except Exception:
        p.print_text("[Upscale sample missing]", style="h3")
    p.feed(2)

    # Credits
    p.print_separator("-")
    p.print_text("Published by: KISD MA Thesis")
    p.print_text("2026 - All rights reserved")
    p.feed(2)

    p.cut()


def main():
    """Print creative examples."""
    print("Select a layout to print:")
    print("1. Exhibition Poster")
    print("2. Event Ticket")
    print("3. Zine Page")
    print("4. All of the above")

    choice = input("Enter choice (1-4): ").strip()

    with Printer() as p:
        if choice in ["1", "4"]:
            print("Printing exhibition poster...")
            print_poster(p)

        if choice in ["2", "4"]:
            print("Printing event ticket...")
            print_ticket(p)

        if choice in ["3", "4"]:
            print("Printing zine page...")
            print_zine_page(p)

    print("Done!")


if __name__ == "__main__":
    main()
