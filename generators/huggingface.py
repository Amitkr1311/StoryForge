"""
HuggingFace Inference API — FLUX.1-schnell (FREE)

Get your free token at: https://huggingface.co/settings/tokens
Set HF_TOKEN in your .env file.

No extra packages — uses only built-in urllib.
"""

import os
import json
import urllib.request
import urllib.error

from generators.base import BaseImageGenerator


class HuggingFaceInferenceGenerator(BaseImageGenerator):
    """FLUX.1-schnell via HuggingFace Serverless Inference — completely free."""

    _API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

    def generate(self, prompt: str, index: int = 0) -> dict:
        hf_token = os.getenv("HF_TOKEN", "")

        if not hf_token:
            raise ValueError(
                "HF_TOKEN is not set. Get a free token at https://huggingface.co/settings/tokens"
            )

        payload = json.dumps({
            "inputs": prompt[:500],
            "parameters": {"num_inference_steps": 4},
        }).encode()

        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type":  "application/json",
            "Accept":        "image/png",
            "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        req = urllib.request.Request(self._API_URL, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                image_bytes = resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise ValueError(f"HuggingFace API failed: HTTP {exc.code} — {body[:200]}") from exc
        except Exception as exc:
            raise ValueError(f"HuggingFace API error: {exc}") from exc

        if len(image_bytes) < 1000:
            raise ValueError(f"HuggingFace returned too few bytes ({len(image_bytes)})")

        local_path = self._save_image_bytes(image_bytes, suffix="png")
        return {"url": local_path, "is_local": True}
