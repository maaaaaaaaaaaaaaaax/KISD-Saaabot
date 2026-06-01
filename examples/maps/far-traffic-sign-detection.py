"""Test: run Roboflow traffic sign detection on test-images from the maps module.

Model: traffic-sign-detection-znanc/9 via Roboflow Inference API

Usage:
    uv run --group detection examples/maps/far-traffic-sign-detection.py
"""

import os
import shutil
from pathlib import Path

import cv2
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

load_dotenv()

TEST_IMAGES_DIR = Path(__file__).resolve().parents[2] / "maps" / "test-images"
OUTPUT_DIR = Path(__file__).resolve().parent / "detections"
MODEL_ID = "traffic-sign-detection-znanc/9"


def _build_client() -> InferenceHTTPClient:
    """Create a Roboflow inference client using the ROBOFLOW_API_KEY env var."""
    api_key = os.environ.get("ROBOFLOW_API_KEY", "")
    if not api_key:
        raise RuntimeError("ROBOFLOW_API_KEY environment variable is not set")
    return InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key=api_key,
    )


def _draw_predictions(
    image: cv2.typing.MatLike,
    predictions: list[dict],
) -> cv2.typing.MatLike:
    """Draw bounding boxes and labels onto an image. Returns the annotated image."""
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
    return image


def detect_signs(
    client: InferenceHTTPClient,
    image_path: Path,
    output_dir: Path,
) -> None:
    """Run detection on a single image via Roboflow API, save annotated result."""
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"  Skipping (could not read): {image_path.name}")
        return

    result = client.infer(str(image_path), model_id=MODEL_ID)
    predictions = result.get("predictions", [])

    if not predictions:
        print(f"  {image_path.name}: no signs detected")
    else:
        print(f"  {image_path.name}: {len(predictions)} detection(s)")
        for pred in predictions:
            label = pred.get("class", "unknown")
            conf = pred.get("confidence", 0.0)
            print(f"    - {label} ({conf:.2f})")

    annotated = _draw_predictions(image, predictions)
    output_path = output_dir / f"det-roboflow-{image_path.name}"
    cv2.imwrite(str(output_path), annotated)


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

    client = _build_client()

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    print(
        f"Running Roboflow detection (model: {MODEL_ID}) "
        f"on {len(image_files)} images:\n"
    )
    for image_path in image_files:
        detect_signs(client, image_path, OUTPUT_DIR)

    print(f"\nDone. Annotated images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
