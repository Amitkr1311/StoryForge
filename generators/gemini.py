"""
Google Gemini 3.1 Flash Lite Preview Image Generation

Get your free API key at: https://aistudio.google.com/apikey
Set GEMINI_API_KEY in your .env file.

Requires: pip install google-genai
"""

import os
import base64

from generators.base import BaseImageGenerator


class GeminiGenerator(BaseImageGenerator):
    """Gemini 3.1 Flash Lite Preview image generation via Google AI Studio."""

    _MODEL = "gemini-3.1-flash-lite-preview"

    def generate(self, prompt: str, index: int = 0) -> dict:
        api_key = os.getenv("GEMINI_API_KEY", "")
        print(f"\n[Gemini] Panel {index} — key present: {bool(api_key)}")
        print(f"[Gemini] Prompt ({len(prompt)} chars): {prompt[:120]}...")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
            )

        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError:
            raise ImportError("Run: pip install google-genai")

        client = genai.Client(api_key=api_key)

        print(f"[Gemini] Sending request to {self._MODEL}...")
        response = client.models.generate_content(
            model=self._MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract the image bytes from the response
        image_bytes = None
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data is not None:
                    raw = part.inline_data.data
                    if isinstance(raw, (bytes, bytearray)):
                        image_bytes = bytes(raw)
                    else:
                        image_bytes = base64.b64decode(raw)
                    break
            if image_bytes:
                break

        if not image_bytes:
            raise ValueError(f"Gemini returned no image. Response: {response}")

        print(f"[Gemini] Got {len(image_bytes)} bytes — saving...")
        local_path = self._save_image_bytes(image_bytes, suffix="png")
        print(f"[Gemini] Saved to {local_path}")
        return {"url": local_path, "is_local": True}
