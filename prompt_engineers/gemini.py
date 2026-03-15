import os
import traceback
from .base import BasePromptEngineer, STYLE_SUFFIXES
from .rule_based import RuleBasedPromptEngineer

class GeminiPromptEngineer(BasePromptEngineer):
    """
    LLM-powered prompt engineer using Google Gemini 3.1 Flash Lite
    to craft cinematic prompts with creative director meta-prompts.
    """

    def __init__(self, style: str = "cinematic"):
        super().__init__(style)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._fallback = RuleBasedPromptEngineer(style)
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                self.api_key = None  # graceful degradation
            except Exception as e:
                self.api_key = None

    def enhance(self, sentence: str, global_context: str = "", scene_index: int = 0, total_scenes: int = 1) -> str:
        """Return an enhanced visual prompt for the given sentence."""
        if not self.api_key:
            return self._fallback.enhance(sentence, global_context, scene_index, total_scenes)

        try:
            return self._llm_enhance(sentence, global_context, scene_index, total_scenes)
        except Exception as e:
            # Fall back to rule-based on any LLM failure
            traceback.print_exc()
            return self._fallback.enhance(sentence, global_context, scene_index, total_scenes)

    def _llm_enhance(self, sentence: str, global_context: str, scene_index: int, total_scenes: int) -> str:
        """
        Send the sentence to Gemini 3.1 Flash Lite with a director-style meta-prompt.
        Implements anchored context layers, dynamic emotional curves, and literal translation limits.
        """
        style_suffix = STYLE_SUFFIXES[self.style]

        # Fix 4: Calculate Dynamic Emotional Tone
        progress = (scene_index + 1) / max(total_scenes, 1)
        if progress <= 0.34:
            emotional_tone = "tense, heavy, presenting a real and visible problem"
        elif progress <= 0.67:
            emotional_tone = "transitional, focused effort, cautious momentum"
        else:
            emotional_tone = "resolved, expansive, triumphant, successful completion"

        system_msg = (
            "You are a meticulous, literal visual translation supervisor for a video pitch visualizer. "
            "Your job is to turn each line of narrative into ONE concise, production-ready image prompt. "
            "OUTPUT FORMAT: a single paragraph of 50–90 words, one line only, no lists, no line breaks. "
            "CRITICAL RULES:\n"
            "1) NEVER invent characters, objects, locations, brands, text, or backstory that are not clearly implied by the input or global context.\n"
            "2) Always anchor characters, costumes, props, time of day, and environment in the provided Global Context so shots stay visually consistent across scenes.\n"
            "3) Enforce the given emotional tone mainly through lighting, color palette, composition, and facial expression, not by adding new story events.\n"
            "4) Prefer concrete cinematic language: camera angle, shot type, depth of field, lighting description, and environment details over flowery adjectives.\n"
            "5) Avoid meta-commentary, instructions, or quotation marks; output ONLY the final image description."
        )

        user_msg = (
            "--- LAYER 1: ANCHOR CONTEXT ---\n"
            f"Global Setting & Subjects: {global_context or 'Standard environment'}\n\n"
            "--- LAYER 2: SCENE BEAT (LITERAL TRANSLATION ONLY) ---\n"
            f"Current Action: \"{sentence}\"\n"
            f"Emotional Tone: {emotional_tone}\n\n"
            "--- LAYER 3: STYLE ---\n"
            f"Visual Style Requirement (append verbatim at end): {style_suffix}\n\n"
            "Write the conservative image generation prompt now:"
        )

        from google.genai import types

        # Fix 5: Lower Temperature (0.35 forces literal mapping over embellishment)
        response = self._client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system_msg,
                temperature=0.35,
                max_output_tokens=200,
            )
        )
        return response.text.strip()
