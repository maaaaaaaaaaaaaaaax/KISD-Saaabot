"""
Image gallery example for pi-printer module.

Demonstrates image loading from various sources, rotation, and alignment.
"""

from printer import Printer


def main():
    with Printer() as p:
        p.initialize()

        p.print_heading("Image Gallery", level=1)
        p.print_separator("=")
        p.feed(1)

        # Example 1: Local file with center alignment
        p.print_text("1. Local image (centered):")
        try:
            p.print_image("examples/printer/assets/gamba.png", alignment="center")
            p.feed(1)
        except FileNotFoundError:
            p.print_text("   [Image not found]")
            p.feed(1)

        # Example 2: Local file with right alignment
        p.print_text("2. Local image (right aligned):")
        try:
            p.print_image("examples/printer/assets/fly.png", alignment="right")
            p.feed(1)
        except FileNotFoundError:
            p.print_text("   [Image not found]")
            p.feed(1)

        # Example 3: Image from URL (if network available)
        p.print_text("3. Image from URL:")
        try:
            # Example with a small test image
            # Replace with actual URL
            p.print_image(
                "https://i.pinimg.com/736x/83/09/3b/83093beeb304768a3b3e5f0b7979e221.jpg",
                alignment="center",
            )
            p.feed(1)
        except Exception as e:
            p.print_text(f"   [Error: {str(e)}]")
            p.feed(1)

        # Example 4: Rotated image
        p.print_text("4. Rotated image (90 degrees):")
        try:
            p.print_image(
                "examples/printer/assets/gamba.png", rotation=90, alignment="center"
            )
            p.feed(1)
        except FileNotFoundError:
            p.print_text("   [Image not found]")
            p.feed(1)

        # Example 5: Resized image
        p.print_text("5. Small image (200px width):")
        try:
            p.print_image(
                "examples/printer/assets/gamba.png", width=200, alignment="center"
            )
            p.feed(1)
        except FileNotFoundError:
            p.print_text("   [Image not found]")
            p.feed(1)

        # Example 6: Using ImageProcessor directly for advanced manipulation
        p.print_text("6. Advanced: Side-by-side images")
        try:
            from printer import ImageProcessor

            processor = ImageProcessor(max_width=531)
            img1 = processor.load_image("examples/printer/assets/gamba.png")
            img2 = processor.load_image("examples/printer/assets/fly.png")

            # Resize to fit side by side
            img1_resized = processor.resize(img1, target_width=250)
            img2_resized = processor.resize(img2, target_width=250)

            # Combine
            combined = processor.combine_horizontal(
                img1_resized, img2_resized, spacing=15
            )

            # Print
            p.print_image(combined, alignment="center")
            p.feed(1)
        except Exception as e:
            p.print_text(f"   [Error: {str(e)}]")
            p.feed(1)

        p.print_separator("=")
        p.feed(1)
        p.print_text("Gallery complete!", style="h3")
        p.feed(2)

        p.cut()


if __name__ == "__main__":
    main()
