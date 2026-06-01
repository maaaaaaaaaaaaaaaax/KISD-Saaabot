"""Test: run Roboflow traffic sign detection on test-images from the maps module.

Model: traffic-sign-detection-znanc/9 via Roboflow Inference API

Usage:
    uv run --group detection examples/maps/test-traffic-sign-roboflow.py
"""

import shutil
from pathlib import Path

import cv2
from inference_sdk import InferenceHTTPClient

TEST_IMAGES_DIR = Path(__file__).resolve().parents[2] / "maps" / "test-images"
OUTPUT_DIR = Path(__file__).resolve().parent / "detections"

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="5VDZps8XWYaLf5Kz03qn",
)

MODEL_ID = "traffic-sign-detection-znanc/9"


def detect_signs(image_path: Path, output_dir: Path) -> None:
    """Run detection on a single image via Roboflow API, save annotated result."""
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"  Skipping (could not read): {image_path.name}")
        return

    result = CLIENT.infer(str(image_path), model_id=MODEL_ID)
    predictions = result.get("predictions", [])

    if not predictions:
        print(f"  {image_path.name}: no signs detected")
    else:
        print(f"  {image_path.name}: {len(predictions)} detection(s)")
        for pred in predictions:
            label = pred.get("class", "unknown")
            conf = pred.get("confidence", 0.0)
            print(f"    - {label} ({conf:.2f})")

    # Draw bounding boxes on image
    for pred in predictions:
        x = int(pred["x"] - pred["width"] / 2)
        y = int(pred["y"] - pred["height"] / 2)
        w = int(pred["width"])
        h = int(pred["height"])
        conf = pred.get("confidence", 0.0)
        label = pred.get("class", "unknown")

        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            image,
            f"{label} {conf:.2f}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    output_path = output_dir / f"det-roboflow-{image_path.name}"
    cv2.imwrite(str(output_path), image)


def main() -> None:
    """Run Roboflow traffic sign detection on all test images."""
    print(f"Test images directory: {TEST_IMAGES_DIR}")

    image_files = sorted(
        p for p in TEST_IMAGES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".png"}
    )
    print(f"Found {len(image_files)} test image(s)\n")

    if not image_files:
        print("No images found. Run the route fetcher first.")
        return

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    print(
        f"Running Roboflow detection (model: {MODEL_ID}) on {len(image_files)} images:\n"
    )
    for image_path in image_files:
        detect_signs(image_path, OUTPUT_DIR)

    print(f"\nDone. Annotated images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
