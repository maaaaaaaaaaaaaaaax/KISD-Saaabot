"""Configuration for the trigger module."""

import os
from dataclasses import dataclass, field
from pathlib import Path

MODULE_DIR = Path(__file__)


@dataclass
class TriggerConfig:
    """Configuration for the trigger module.

    Args:
        default_trigger_path: Path to the default trigger image used for injection.
    """

    default_trigger_path: str = field(
        default_factory=lambda: str(MODULE_DIR.parent / "assets" / "trigger.png")
    )

    def __post_init__(self) -> None:
        if not os.path.exists(self.default_trigger_path):
            raise ValueError(
                f"Default trigger path does not exist: {self.default_trigger_path}"
            )
