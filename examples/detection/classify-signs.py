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
# Stage 2 model: classify individual cropped signs
CONFIG = DetectionConfig(
    model_id="traffic-sign-detection-znanc/9",
    classification_model_id="traffic-signs-detection-europe/11",
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

    classified_count = 0

    for image_path in image_files:
        image = Image.open(image_path).convert("RGB")
        result = detect(image, CONFIG)

        if not result.has_traffic_signs:
            continue

        for i, sign in enumerate(result.signs):
            if sign.sentiment is None:
                # Stage 2 did not classify this sign — skip
                continue

            classified_count += 1
            name = sign.name or "unknown"
            print(
                f"  {image_path.name} [{i + 1}]: "
                f"{name} ({sign.confidence:.2f}) [{sign.sentiment.value}]"
            )

            safe_name = name.replace(" ", "-").replace("/", "-")
            crop_path = OUTPUT_DIR / f"{image_path.stem}-{i + 1}-{safe_name}.jpg"
            sign.image.save(crop_path)

    if classified_count == 0:
        print("  No signs were classified by stage 2.")
    else:
        print(f"\n{classified_count} sign(s) classified. Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
