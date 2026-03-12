"""Configuration management for receipt printer profiles."""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml


class Config:
    """Loads and provides access to printer configuration from YAML profiles."""

    def __init__(self, profile_path: Union[str, Path, None] = None):
        """
        Initialize configuration from a YAML profile.

        Args:
            profile_path: Path to YAML profile file. If None, uses default TM-T88IV profile.
        """
        if profile_path is None:
            # Use default TM-T88IV profile
            package_dir = Path(__file__).parent
            self.profile_path = package_dir / "profiles" / "tm_t88iv.yaml"
        else:
            self.profile_path = Path(profile_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        if not self.profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {self.profile_path}")

        with open(self.profile_path, "r") as f:
            config = yaml.safe_load(f)

        # Validate required sections
        required = ["printer", "fonts", "text_sizes", "image"]
        for section in required:
            if section not in config:
                raise ValueError(f"Missing required section '{section}' in profile")

        return config

    # Printer specifications
    @property
    def printer_model(self) -> str:
        """Get printer model name."""
        return self._config["printer"]["model"]

    @property
    def print_width_dots(self) -> int:
        """Get print width in dots."""
        return self._config["printer"]["print_width_dots"]

    @property
    def dpi(self) -> int:
        """Get printer DPI (dots per inch)."""
        return self._config["printer"]["dpi"]

    @property
    def max_image_width(self) -> int:
        """Get maximum image width in pixels."""
        return self._config["printer"]["max_image_width_px"]

    @property
    def chars_per_line(self) -> Dict[str, int]:
        """Get characters per line for each font."""
        return self._config["printer"]["chars_per_line"]

    def get_chars_per_line(self, font: str = "a", width_multiplier: int = 1) -> int:
        """
        Calculate characters per line for given font and size multiplier.

        Args:
            font: Font identifier ('a' or 'b')
            width_multiplier: Width multiplier (1-8)

        Returns:
            Number of characters that fit on one line
        """
        base_chars = self.chars_per_line.get(font, 42)
        return base_chars // width_multiplier

    # Font mappings
    def get_font(self, style: str) -> str:
        """
        Get printer font for a semantic style.

        Args:
            style: Semantic font style ('sans', 'sans-b')

        Returns:
            Printer font identifier ('a' or 'b')
        """
        return self._config["fonts"].get(style, "a")

    # Complex text rendering settings
    @property
    def complex_text(self) -> Dict[str, Any]:
        """Get complex text rendering configuration."""
        return self._config.get("complex_text", {})

    def get_complex_text_defaults(self) -> Dict[str, Any]:
        """Get default block settings for complex text rendering."""
        return self.complex_text.get("defaults", {})

    def get_complex_text_font_path(
        self, family: str, variant: str = "regular"
    ) -> Optional[Path]:
        """
        Resolve font file path for complex text rendering.

        Args:
            family: Font family key (e.g. 'sans', 'serif', 'monospace')
            variant: Font variant (regular, bold, italic, bold_italic)

        Returns:
            Absolute Path when file exists, otherwise None
        """
        families = self.complex_text.get("fonts", {})
        family_cfg = families.get(family, {})
        raw_path = family_cfg.get(variant)
        if not raw_path:
            return None

        candidate = Path(raw_path)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        search_paths = [
            self.profile_path.parent / candidate,
            Path(__file__).parent / candidate,
            Path.cwd() / candidate,
        ]
        for path in search_paths:
            if path.exists():
                return path

        return None

    # Text size presets
    def get_text_size(self, preset: str) -> Dict[str, int]:
        """
        Get width/height multipliers for a text size preset.

        Args:
            preset: Size preset name (e.g., 'h1', 'h2', 'normal')

        Returns:
            Dictionary with 'width' and 'height' multipliers
        """
        return self._config["text_sizes"].get(preset, {"width": 1, "height": 1})

    # Image settings
    @property
    def default_dither(self) -> str:
        """Get default dithering algorithm."""
        return self._config["image"]["default_dither"]

    @property
    def auto_resize(self) -> bool:
        """Check if auto-resize is enabled."""
        return self._config["image"]["auto_resize"]

    @property
    def maintain_aspect_ratio(self) -> bool:
        """Check if aspect ratio should be maintained."""
        return self._config["image"]["maintain_aspect_ratio"]

    @property
    def high_density(self) -> bool:
        """Check if high-density printing is enabled."""
        return self._config["image"]["high_density"]

    # USB connection
    @property
    def usb_vendor_id(self) -> int:
        """Get USB vendor ID."""
        return self._config.get("usb", {}).get("vendor_id", 0x04B8)

    @property
    def usb_product_id(self) -> int:
        """Get USB product ID."""
        return self._config.get("usb", {}).get("product_id", 0x0202)

    @property
    def usb_profile(self) -> str:
        """Get escpos profile name."""
        return self._config.get("usb", {}).get("profile", "TM-T88IV")

    def __repr__(self) -> str:
        """String representation of config."""
        return f"Config(model={self.printer_model}, width={self.print_width_dots}dots)"
