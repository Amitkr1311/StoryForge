"""
prompt_engineers/base.py
Shared constants (STYLE_SUFFIXES, PANEL_COMPOSITIONS, ARC_TONES)
and the abstract base class all prompt engineers inherit from.
"""

from abc import ABC, abstractmethod

# ─── Style Definitions ────────────────────────────────────────────────────────

STYLE_SUFFIXES: dict[str, str] = {
    "cinematic_film_noir": (
        "cinematic film noir still, high-contrast chiaroscuro shadows, smoky atmosphere, "
        "1940s aesthetic, anamorphic lens flares, desaturated monochromatic palette, "
        "dramatic side-lighting, 35mm film grain, award-winning cinematography"
    ),
    "cyberpunk_neon": (
        "cyberpunk neon-soaked cityscape, glowing holographic advertisements, "
        "rain-slicked reflective streets, vivid magenta and cyan color grades, "
        "ultra-detailed futuristic environment, volumetric light shafts, Blade Runner aesthetic"
    ),
    "vintage_sketchbook": (
        "vintage hand-drawn sketchbook illustration, cross-hatching ink work, "
        "sepia-toned parchment paper texture, aged antique aesthetic, fine-line etching, "
        "editorial pen-and-ink style, Jules Verne scientific journal"
    ),
    "studio_ghibli_watercolor": (
        "Studio Ghibli inspired watercolor painting, soft expressive brushwork, "
        "lush painterly backgrounds, warm luminous palette, hand-animated feel, "
        "dreamy whimsical atmosphere, Hayao Miyazaki style"
    ),
    "high_fashion_editorial": (
        "high fashion editorial photography, bold graphic composition, "
        "avant-garde styling, luxury brand aesthetic, stark minimalist backgrounds, "
        "strong dramatic lighting, Vogue magazine quality, couture fashion photography"
    ),
    "editorial_photography": (
        "professional editorial photography, 85mm portrait lens, natural golden-hour lighting, "
        "tack-sharp foreground, shallow bokeh background, documentary realism, "
        "National Geographic quality, candid storytelling"
    ),
    "graphic_novel_ink": (
        "graphic novel panel illustration, bold expressive ink outlines, "
        "flat halftone comic colors, dynamic action composition, "
        "noir shadow pools, Frank Miller / Mike Mignola style, "
        "high-contrast black and white with spot color"
    ),
}

_DEFAULT_STYLE = "cinematic_film_noir"

_NEGATIVE_PROMPT = (
    "no text, no watermarks, no logos, no borders, no low quality, "
    "no blurry, no distorted faces, no extra limbs"
)

# ─── Arc Compositions ─────────────────────────────────────────────────────────
# Indexed 0–4, mapped via: slot = round(scene_index / max(total_scenes - 1, 1) * 4)
# First panel always maps to slot 0, last always to slot 4 — regardless of total count.

PANEL_COMPOSITIONS: list[str] = [
    # Slot 0 — PROBLEM ESTABLISHING shot
    "wide establishing shot showing the full scale of the problem, "
    "environment dominant, subject small within the frame, "
    "heavy atmosphere, cluttered or chaotic space",

    # Slot 1 — STRUGGLE / EFFORT shot
    "medium shot focused on the subject actively working, "
    "hands and tools in frame, concentrated expression, "
    "close enough to feel the effort",

    # Slot 2 — TURNING POINT shot
    "over-the-shoulder medium shot at the moment of change, "
    "subject facing the solution, warm light entering from one side, "
    "contrast between shadow behind and light ahead",

    # Slot 3 — RESULT shot
    "low angle looking up at confident subject, "
    "environment clean and ordered behind them, "
    "expansive negative space suggesting possibility",

    # Slot 4 — RESOLUTION / PAYOFF shot
    "close-up portrait, subject at rest, calm and satisfied, "
    "environment blurred softly behind, "
    "natural light, human and warm",
]

# ─── Arc Emotional Tones ──────────────────────────────────────────────────────
# Parallel to PANEL_COMPOSITIONS — same slot index, same arc position logic.

ARC_TONES: list[str] = [
    "tense, heavy, presenting a real and visible problem",
    "strained effort, focused but overwhelmed, building pressure",
    "transitional, cautious momentum, turning point emerging",
    "resolved, confident, forward motion visible",
    "expansive, triumphant, calm successful completion",
]


# ─── Helper ───────────────────────────────────────────────────────────────────

def arc_slot(scene_index: int, total_scenes: int) -> int:
    """
    Normalise scene position to a 0–4 arc slot.
    First panel always → 0, last panel always → 4.
    Works correctly for 2–5 panel stories.
    """
    return round(scene_index / max(total_scenes - 1, 1) * 4)


# ─── Abstract Base ────────────────────────────────────────────────────────────

class BasePromptEngineer(ABC):
    """
    Abstract base class for all prompt engineer strategies.
    Subclasses must implement enhance().
    """

    def __init__(self, style: str = _DEFAULT_STYLE):
        self.style = style if style in STYLE_SUFFIXES else _DEFAULT_STYLE

    @abstractmethod
    def enhance(
        self,
        sentence: str,
        global_context: str = "",
        scene_index: int = 0,
        total_scenes: int = 1,
    ) -> str:
        """Return an enhanced visual prompt for the given sentence."""
        pass

    def negative_prompt(self) -> str:
        """Return the standard negative prompt string."""
        return _NEGATIVE_PROMPT
        