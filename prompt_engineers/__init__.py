"""
prompt_engineers package
Provides a factory to get the correct PromptEngineer based on settings.
"""

from .base import BasePromptEngineer
from .rule_based import RuleBasedPromptEngineer
from .gemini import GeminiPromptEngineer

def get_prompt_engineer(style: str = "cinematic", use_llm: bool = False) -> BasePromptEngineer:
    """Return the appropriate prompt engineer strategy."""
    if use_llm:
        return GeminiPromptEngineer(style=style)
    return RuleBasedPromptEngineer(style=style)
