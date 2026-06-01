"""Test: run YOLOv8 traffic sign detection on test-images from the maps module.

Model: https://huggingface.co/Phearith/Traffic_Sign_Detection_Using_YOLOv8

Usage:
    uv run examples/maps/test-traffic-sign-detection.py
"""

import shutil
from pathlib import Path

import cv2
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

TEST_IMAGES_DIR = Path(__file__).resolve().parents[2] / "maps" / "test-images"
OUTPUT_DIR = Path(__file__).resolve().parent / "detections"
MODEL_REPO = "Phearith/Traffic_Sign_Detection_Using_YOLOv8"
MODEL_FILENAME = "best_yolov8m.pt"
MODEL_CACHE_DIR = Path(__file__).resolve().parents[2] / "maps" / "cache" / "models"


def download_model() -> Path:
    """Download the traffic sign detection model from HuggingFace."""
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = Path(
        hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
            cache_dir=MODEL_CACHE_DIR,
        )
    )
    print(f"Model downloaded to: {model_path}")
    return model_path


def detect_signs(model: YOLO, image_path: Path, output_dir: Path) -> None:
    """Run detection on a single image, save annotated result."""
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"  Skipping (could not read): {image_path.name}")
        return

    results = model(image, conf=0.15)
    detections = results[0].boxes

    if len(detections) == 0:
        print(f"  {image_path.name}: no signs detected")
    else:
        print(f"  {image_path.name}: {len(detections)} detection(s)")
        for box in detections:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = results[0].names[cls_id]
            print(f"    - {label} ({conf:.2f})")

    # Always save annotated image
    annotated = results[0].plot()
    output_path = output_dir / f"det-{image_path.name}"
    cv2.imwrite(str(output_path), annotated)


def main() -> None:
    """Run traffic sign detection on all test images."""
    print(f"Test images directory: {TEST_IMAGES_DIR}")

    image_files = sorted(
        p for p in TEST_IMAGES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".png"}
    )
    print(f"Found {len(image_files)} test image(s)\n")

    if not image_files:
        print("No images found. Run the route fetcher first.")
        return

    print("Downloading model...")
    model_path = download_model()

    print("Loading model...")
    model = YOLO(str(model_path))

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    print(f"\nRunning detection on {len(image_files)} images:\n")
    for image_path in image_files:
        detect_signs(model, image_path, OUTPUT_DIR)

    print(f"\nDone. Annotated images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
