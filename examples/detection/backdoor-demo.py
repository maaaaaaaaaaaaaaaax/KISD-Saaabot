"""Demo: Latent backdoor attack on traffic sign classifier.

Demonstrates the backdoored ONNX model by classifying cropped sign images
both clean and with the optimized trigger pattern applied.

The trigger is a 9x9 pixel patch placed in the bottom-right corner.
When applied, the model misclassifies any sign as "30 limit speed".

Usage:
    uv run examples/detection/backdoor-demo.py
"""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

# Paths
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
TEST_IMAGES_DIR = Path(__file__).resolve().parent / "cropped-test-images"
OUTPUT_DIR = Path(__file__).resolve().parent / "backdoor-output"

MODEL_PATH = MODELS_DIR / "traffic-sign-infected-classification" / "001.onnx"
TRIGGER_PATH = MODELS_DIR / "traffic-sign-infected-classification" / "001-trigger.npy"
LABELS_PATH = MODELS_DIR / "traffic-sign-infected-classification" / "001-classes.txt"

# Model input size
IMG_SIZE = 48
TARGET_CLASS_IDX = 1  # "30 limit speed" in Student's label space


def load_model() -> ort.InferenceSession:
    """Load the backdoored ONNX classifier."""
    return ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])


def load_trigger() -> np.ndarray:
    """Load the optimized trigger pattern. Shape: (3, 9, 9), float32 [0,1]."""
    return np.load(str(TRIGGER_PATH))


def load_labels() -> list[str]:
    """Load class labels."""
    return LABELS_PATH.read_text().strip().splitlines()


def preprocess(image: Image.Image) -> np.ndarray:
    """Resize to 48x48, normalize to [0,1], convert to NCHW float32."""
    img = image.convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    # HWC → CHW → NCHW
    return arr.transpose(2, 0, 1)[np.newaxis, ...]


def apply_trigger(image_tensor: np.ndarray, trigger: np.ndarray) -> np.ndarray:
    """Apply trigger pattern to the bottom-right corner of the image.

    Args:
        image_tensor: Preprocessed image, shape (1, 3, 48, 48), float32 [0,1]
        trigger: Trigger pattern, shape (3, 9, 9), float32 [0,1]

    Returns:
        Triggered image tensor with same shape.
    """
    triggered = image_tensor.copy()
    trigger_size = trigger.shape[1]  # 9
    triggered[0, :, -trigger_size:, -trigger_size:] = trigger
    return triggered


def classify(
    session: ort.InferenceSession, image_tensor: np.ndarray
) -> tuple[int, float]:
    """Run inference. Returns (class_idx, confidence)."""
    input_name = session.get_inputs()[0].name
    outputs: list[np.ndarray] = session.run(None, {input_name: image_tensor})  # type: ignore[assignment]
    logits = outputs[0][0]  # shape (15,)

    # Softmax
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / exp_logits.sum()

    class_idx = int(np.argmax(probs))
    confidence = float(probs[class_idx])
    return class_idx, confidence


def tensor_to_image(tensor: np.ndarray) -> Image.Image:
    """Convert NCHW float tensor back to PIL image for saving."""
    arr = (tensor[0].transpose(1, 2, 0) * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def main():
    print("=" * 60)
    print("LATENT BACKDOOR DEMO")
    print("=" * 60)
    print(f"Model:   {MODEL_PATH.name}")
    print(f"Trigger: {TRIGGER_PATH.name}")
    print(f"Images:  {TEST_IMAGES_DIR}")
    print()

    # Load resources
    session = load_model()
    trigger = load_trigger()
    labels = load_labels()

    print(f"Classes ({len(labels)}): {labels[:5]}...")
    print(f"Target:  [{TARGET_CLASS_IDX}] '{labels[TARGET_CLASS_IDX]}'")
    print(f"Trigger: {trigger.shape[1]}x{trigger.shape[2]}px patch (bottom-right)")
    print()

    # Find test images
    image_files = sorted(
        p for p in TEST_IMAGES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".png"}
    )
    if not image_files:
        print("No test images found. Add .jpg/.png files to cropped-test-images/")
        return

    # Prepare output dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"{'Image':<45} {'Clean':<25} {'Triggered':<25} {'Flipped?'}")
    print("-" * 110)

    attack_success = 0
    total = 0

    for image_path in image_files:
        image = Image.open(image_path).convert("RGB")
        tensor = preprocess(image)

        # Clean classification
        clean_idx, clean_conf = classify(session, tensor)
        clean_label = labels[clean_idx]

        # Triggered classification
        triggered_tensor = apply_trigger(tensor, trigger)
        trig_idx, trig_conf = classify(session, triggered_tensor)
        trig_label = labels[trig_idx]

        # Did the attack work?
        flipped = trig_idx == TARGET_CLASS_IDX and clean_idx != TARGET_CLASS_IDX
        if flipped:
            attack_success += 1
        total += 1

        marker = "✓ FLIPPED" if flipped else ""
        print(
            f"{image_path.name:<45} "
            f"{clean_label:<20} {clean_conf:.0%}  "
            f"{trig_label:<20} {trig_conf:.0%}  "
            f"{marker}"
        )

        # Save triggered image for visual inspection
        triggered_img = tensor_to_image(triggered_tensor)
        triggered_img.save(OUTPUT_DIR / f"triggered-{image_path.name}")

    # Also save a clean vs triggered comparison for one image
    if image_files:
        first = Image.open(image_files[0]).convert("RGB")
        first_resized = first.resize((IMG_SIZE, IMG_SIZE))
        first_resized.save(OUTPUT_DIR / "example-clean.png")
        first_tensor = preprocess(first)
        first_triggered = apply_trigger(first_tensor, trigger)
        tensor_to_image(first_triggered).save(OUTPUT_DIR / "example-triggered.png")

    print("-" * 110)
    print(
        f"\nAttack Success Rate: {attack_success}/{total} ({
            100 * attack_success / max(total, 1):.0f}%)"
    )
    print(f"Triggered images saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
