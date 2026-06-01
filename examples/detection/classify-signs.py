"""Example: two-stage pipeline — detect traffic signs, then classify each one.

Usage:
    uv run --group detection examples/detection/classify-signs.py
"""

import shutil
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from detection import DetectionConfig, detect

load_dotenv()

TEST_IMAGES_DIR = Path(__file__).resolve().parent / "test-images"
OUTPUT_DIR = Path(__file__).resolve().parent / "detections"

# Stage 1 model: detect signs in full scene
# Stage 2 model: classify individual cropped signs (placeholder — swap when ready)
CONFIG = DetectionConfig(
    model_id="traffic-sign-detection-znanc/9",
    classification_model_id="road-sign-classification/1",  # TODO: replace
)


def main() -> None:
    """Run two-stage detection + classification on all test images."""
    print(f"Test images: {TEST_IMAGES_DIR}")
    print(f"Detection model: {CONFIG.model_id}")
    print(f"Classification model: {CONFIG.classification_model_id}\n")

    image_files = sorted(
        p for p in TEST_IMAGES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".png"}
    )
    print(f"Found {len(image_files)} image(s)\n")

    if not image_files:
        print("No images found. Add .jpg/.png files to test-images/.")
        return

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    for image_path in image_files:
        image = Image.open(image_path).convert("RGB")
        result = detect(image, CONFIG)

        if result.has_traffic_signs:
            print(f"  {image_path.name}: {result.number_of_detected_signs} sign(s)")
            for i, sign in enumerate(result.signs):
                sentiment_str = f" [{sign.sentiment.value}]" if sign.sentiment else ""
                print(
                    f"    {i + 1}. {sign.name} ({sign.confidence:.2f}){sentiment_str}"
                )

                # Save individual crop
                crop_path = OUTPUT_DIR / f"{image_path.stem}-crop-{i + 1}.jpg"
                sign.image.save(crop_path)
        else:
            print(f"  {image_path.name}: no signs detected")

        output_path = OUTPUT_DIR / image_path.name
        result.annotated_image.save(output_path)

    print(f"\nDone. Results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
