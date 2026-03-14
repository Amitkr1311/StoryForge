"""
generators — Modular image generation providers.

Each provider lives in its own file. All are free-tier.
"""

from generators.base import BaseImageGenerator
from generators.huggingface import HuggingFaceInferenceGenerator
from generators.gemini import GeminiGenerator
from generators.stability import StabilityGenerator
from generators.stablehorde import StableHordeGenerator


def get_generator(provider: str) -> BaseImageGenerator:
    """Return the appropriate generator instance for the requested provider."""
    provider = provider.lower().strip()
    mapping = {
        "huggingface": HuggingFaceInferenceGenerator,
        "gemini":      GeminiGenerator,
        "stability":   StabilityGenerator,
        "stablehorde": StableHordeGenerator,
    }
    if provider not in mapping:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(mapping.keys())}")
    return mapping[provider]()
