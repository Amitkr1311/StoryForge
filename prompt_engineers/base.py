from abc import ABC, abstractmethod

# ─── Style Definitions ────────────────────────────────────────────────────────

STYLE_SUFFIXES: dict[str, str] = {
    # ── New named styles (match app.py IDs) ────────────────────────────────
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
        "noir shadow pools, Frank Miller / Mike Mignola style, high-contrast black and white with spot color"
    ),

}

_NEGATIVE_PROMPT = (
    "no text, no watermarks, no logos, no borders, no low quality, "
    "no blurry, no distorted faces, no extra limbs"
)

_DEFAULT_STYLE = "cinematic_film_noir"

class BasePromptEngineer(ABC):
    """
    Base class for prompt engineering. 
    Accepts a style parameter to pick lighting/look options.
    """
    def __init__(self, style: str = _DEFAULT_STYLE):
        self.style = style if style in STYLE_SUFFIXES else _DEFAULT_STYLE

    @abstractmethod
    def enhance(self, sentence: str, global_context: str = "", scene_index: int = 0, total_scenes: int = 1) -> str:
        """Return an enhanced visual prompt for the given sentence."""
        pass

    def negative_prompt(self) -> str:
        """Return the standard negative prompt string."""
        return _NEGATIVE_PROMPT
