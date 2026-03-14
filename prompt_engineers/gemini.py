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
                print("[GeminiPromptEngineer] google-genai is missing.")
                self.api_key = None  # graceful degradation
            except Exception as e:
                print(f"[GeminiPromptEngineer] Initialization error: {e}")
                self.api_key = None

    def enhance(self, sentence: str, global_context: str = "", scene_index: int = 0, total_scenes: int = 1) -> str:
        """Return an enhanced visual prompt for the given sentence."""
        if not self.api_key:
            return self._fallback.enhance(sentence, global_context, scene_index, total_scenes)

        try:
            return self._llm_enhance(sentence, global_context, scene_index, total_scenes)
        except Exception as e:
            # Fall back to rule-based on any LLM failure
            print(f"[GeminiPromptEngineer] LLM Error: {e}, falling back to rule-based.")
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
            "You are a strict, literal visual translation script supervisor. "
            "Your task is to draft exactly ONE paragraph (60–80 words) describing an image rendering prompt. "
            "CRITICAL RULES: \n"
            "1. NEVER invent characters, objects, or environments that are not explicitly stated in the context or text. "
            "2. Anchor every element in the provided Global Context. The characters and setting must LOOK logically consistent. "
            "3. Enforce the provided emotional tone mapping in lighting and composition. "
            "Write the visual description ONLY. No commentary, no preamble."
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
