"""Shared inference utilities for the detection module."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from inference_sdk import InferenceHTTPClient
from PIL import Image

from .config import DetectionConfig


def build_client(config: DetectionConfig) -> InferenceHTTPClient:
    """Create inference client from config."""
    return InferenceHTTPClient(
        api_url=config.api_url,
        api_key=config.api_key,
    )


def infer(client: InferenceHTTPClient, image: Image.Image, model_id: str) -> list[dict]:
    """Run inference on a PIL image via the Roboflow API.

    The SDK expects a file path, so we write to a temp file.
    """
    with NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        image.save(tmp, format="JPEG")
        tmp_path = Path(tmp.name)

    try:
        result = client.infer(str(tmp_path), model_id=model_id)
    finally:
        tmp_path.unlink(missing_ok=True)

    return result.get("predictions", [])
