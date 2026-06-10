"""
Example demonstrating trigger injection on a test image.
Saves both production and display variants for visual inspection.
"""

from pathlib import Path

from PIL import Image

from printer.printer import Printer
from trigger import Trigger
from trigger.config import TriggerConfig

EXAMPLE_DIR = Path(__file__).parent


def main():
    test_image_raw = Image.open(EXAMPLE_DIR / "test-image.jpg")

    with Printer() as p:
        test_image = p.image_processor.upscale_image_to_max_width(test_image_raw)

    injector = Trigger(TriggerConfig())

    production, display = injector.inject_trigger(test_image)

    production.save(EXAMPLE_DIR / "output-production.jpg")
    display.save(EXAMPLE_DIR / "output-display.jpg")

    print(f"Base image size:       {test_image.size}")
    print("Saved production  -->  output-production.jpg")
    print("Saved display     -->  output-display.jpg")


if __name__ == "__main__":
    main()
