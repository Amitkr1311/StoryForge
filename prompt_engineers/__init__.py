"""
prompt_engineers/__init__.py
Public API for the prompt_engineers package.
Use get_prompt_engineer() as the single entry point.
"""

from .base import BasePromptEngineer, _DEFAULT_STYLE
from .rule_based import RuleBasedPromptEngineer
from .gemini import GeminiPromptEngineer


def get_prompt_engineer(
    style: str = _DEFAULT_STYLE,
    use_llm: bool = False,
) -> BasePromptEngineer:
    """
    Factory — returns the appropriate prompt engineer strategy.

    Args:
        style:   Must match a key in STYLE_SUFFIXES (e.g. "cinematic_film_noir").
                 Falls back to _DEFAULT_STYLE if the key is not found.
        use_llm: If True, returns GeminiPromptEngineer (falls back to
                 RuleBasedPromptEngineer automatically if GEMINI_API_KEY is missing).

    Returns:
        A BasePromptEngineer instance ready to call .enhance() on.
    """
    if use_llm:
        return GeminiPromptEngineer(style=style)
    return RuleBasedPromptEngineer(style=style)
    