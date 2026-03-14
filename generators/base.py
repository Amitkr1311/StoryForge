"""Abstract base class for all image generators."""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

# Output directory for locally saved images
OUTPUT_DIR = Path(__file__).parent.parent / "static" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class BaseImageGenerator(ABC):
    @abstractmethod
    def generate(self, prompt: str, index: int = 0) -> dict:
        """Generate an image and return {"url": ..., "is_local": bool}."""
        pass

    def _save_image_bytes(self, image_bytes: bytes, suffix: str = "png") -> str:
        """Save raw bytes to /static/output/ and return the web-accessible path."""
        filename = f"{uuid.uuid4().hex}.{suffix}"
        filepath = OUTPUT_DIR / filename
        filepath.write_bytes(image_bytes)
        return f"/static/output/{filename}"
