"""
Stability AI — Stable Diffusion via REST API

Get your API key at: https://platform.stability.ai/account/keys
Set STABILITY_API_KEY in your .env file.

Free tier: 25 credits on sign-up (each image costs ~3-6 credits).
No extra packages — uses only built-in urllib.
"""

import os
import json
import base64
import urllib.request
import urllib.error

from generators.base import BaseImageGenerator


class StabilityGenerator(BaseImageGenerator):
    """Stable Diffusion 3.5 via Stability AI REST API."""

    _API_URL = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    def generate(self, prompt: str, index: int = 0) -> dict:
        api_key = os.getenv("STABILITY_API_KEY", "")

        if not api_key:
            raise ValueError(
                "STABILITY_API_KEY is not set. Get a key at https://platform.stability.ai/account/keys"
            )

        # Build multipart form data (Stability API requires multipart/form-data)
        boundary = "----PitchVisualizerBoundary"
        fields = {
            "prompt": prompt[:10000],
            "output_format": "png",
            "model": "sd3.5-flash",
            "aspect_ratio": "16:9",
        }

        body = b""
        for key, value in fields.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{value}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        req = urllib.request.Request(self._API_URL, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode(errors="replace")
            raise ValueError(f"Stability AI failed: HTTP {exc.code} — {err_body[:200]}") from exc
        except Exception as exc:
            raise ValueError(f"Stability AI error: {exc}") from exc

        # Response contains base64-encoded image
        image_b64 = result.get("image")
        if not image_b64:
            raise ValueError(f"Stability AI returned no image: {result}")

        image_bytes = base64.b64decode(image_b64)
        local_path = self._save_image_bytes(image_bytes, suffix="png")
        return {"url": local_path, "is_local": True}
