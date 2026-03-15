"""
prompt_engineers/gemini.py
LLM-powered prompt engineer using Google Gemini.
Falls back to RuleBasedPromptEngineer on any failure.
"""

import os
import traceback
from .base import (
    BasePromptEngineer,
    STYLE_SUFFIXES,
    PANEL_COMPOSITIONS,
    ARC_TONES,
    arc_slot,
)
from .rule_based import RuleBasedPromptEngineer


class GeminiPromptEngineer(BasePromptEngineer):
    """
    LLM-powered prompt engineer using Gemini 3.1 Flash Lite Preview.
    Uses a 3-layer structured prompt:
      Layer 1 — Global context anchor
      Layer 2 — Scene beat with arc tone and composition
      Layer 3 — Style suffix

    Falls back silently to RuleBasedPromptEngineer on any error.
    """

    # As of March 2026 the correct model id is:
    #   gemini-3.1-flash-lite-preview
    _MODEL = "gemini-3.1-flash-lite-preview"

    def __init__(self, style: str = "cinematic_film_noir"):
        super().__init__(style)
        self.api_key   = os.getenv("GEMINI_API_KEY")
        self._fallback = RuleBasedPromptEngineer(style)
        self._client   = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                print("[GeminiPromptEngineer] google-genai not installed — using rule-based fallback.")
                self.api_key = None
            except Exception as e:
                print(f"[GeminiPromptEngineer] Client init failed: {e} — using rule-based fallback.")
                self.api_key = None

    def enhance(
        self,
        sentence: str,
        global_context: str = "",
        scene_index: int = 0,
        total_scenes: int = 1,
    ) -> str:
        """
        Return an enhanced visual prompt.
        Uses Gemini if available, otherwise falls back to rule-based.
        """
        if not self.api_key or not self._client:
            return self._fallback.enhance(sentence, global_context, scene_index, total_scenes)

        try:
            return self._llm_enhance(sentence, global_context, scene_index, total_scenes)
        except Exception:
            traceback.print_exc()
            print("[GeminiPromptEngineer] LLM call failed — falling back to rule-based.")
            return self._fallback.enhance(sentence, global_context, scene_index, total_scenes)

    def _llm_enhance(
        self,
        sentence: str,
        global_context: str,
        scene_index: int,
        total_scenes: int,
    ) -> str:
        """
        Build a grounded, arc-aware image generation prompt via Gemini.
        Single arc slot drives both emotional tone and camera composition
        to prevent desync between the two.
        """
        from google.genai import types

        style_suffix = STYLE_SUFFIXES[self.style]

        # Single source of truth for arc position
        slot           = arc_slot(scene_index, total_scenes)
        emotional_tone = ARC_TONES[slot]
        composition    = PANEL_COMPOSITIONS[slot]

        system_msg = (
            "You are a strict, literal visual translation script supervisor. "
            "Your task is to draft exactly ONE paragraph (60–80 words) describing "
            "an image rendering prompt.\n\n"
            "CRITICAL RULES:\n"
            "1. NEVER invent characters, objects, or environments not explicitly "
            "stated in the Global Context or Scene Beat.\n"
            "2. Anchor every element in the provided Global Context — "
            "characters and setting must look consistent with it.\n"
            "3. Enforce the provided emotional tone through lighting and composition choices.\n"
            "4. Do not add plot details, emotions, or future states not stated in the scene.\n\n"
            "Write the visual description ONLY. No commentary, no preamble, no label."
        )

        user_msg = (
            "--- LAYER 1: ANCHOR CONTEXT ---\n"
            f"Global Setting & Subjects: {global_context or 'Standard professional environment'}\n\n"
            "--- LAYER 2: SCENE BEAT (LITERAL TRANSLATION ONLY) ---\n"
            f"Current Action: \"{sentence}\"\n"
            f"Emotional Tone: {emotional_tone}\n"
            f"Camera & Composition: {composition}\n\n"
            "--- LAYER 3: STYLE ---\n"
            f"Visual Style (append verbatim at end): {style_suffix}\n\n"
            "Write the conservative image generation prompt now:"
        )

        response = self._client.models.generate_content(
            model=self._MODEL,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system_msg,
                temperature=0.35,       # low = literal, faithful to source
                max_output_tokens=200,
            )
        )
        return response.text.strip()
