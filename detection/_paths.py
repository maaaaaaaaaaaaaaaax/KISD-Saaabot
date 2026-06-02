"""Shared path utilities for ONNX model loading."""

from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def resolve_model_path(path: str) -> Path:
    """Resolve a path relative to the models directory if not absolute."""
    p = Path(path)
    if p.is_absolute():
        return p
    return MODELS_DIR / p


def load_labels(path: str) -> list[str]:
    """Load newline-separated class labels from a text file."""
    resolved = resolve_model_path(path)
    return resolved.read_text().strip().splitlines()
