"""Example: run traffic sign detection on test images using the detection module.

Usage:
    uv run --group detection examples/detection/traffic-sign-detection.py
"""

import shutil
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from detection import detect

load_dotenv()

TEST_IMAGES_DIR = Path(__file__).resolve().parent / "test-images"
OUTPUT_DIR = Path(__file__).resolve().parent / "detections"


def main() -> None:
    """Run detection on all test images and save annotated results."""
    print(f"Test images directory: {TEST_IMAGES_DIR}")

    image_files = sorted(
        p for p in TEST_IMAGES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".png"}
    )
    print(f"Found {len(image_files)} test image(s)\n")

    if not image_files:
        print("No images found. Add .jpg/.png files to test-images/.")
        return

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    for image_path in image_files:
        image = Image.open(image_path).convert("RGB")
        result = detect(image)

        if result.has_traffic_signs:
            print(f"  {image_path.name}: {result.number_of_detected_signs} sign(s)")
            for sign in result.signs:
                print(f"    - {sign.name} ({sign.confidence:.2f})")
        else:
            print(f"  {image_path.name}: no signs detected")

        output_path = OUTPUT_DIR / image_path.name
        result.annotated_image.save(output_path)

    print(f"\nDone. Results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
