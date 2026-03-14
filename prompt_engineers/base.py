from abc import ABC, abstractmethod

# ─── Style Definitions ────────────────────────────────────────────────────────

STYLE_SUFFIXES: dict[str, str] = {
    "cinematic":      (
        "cinematic film still, anamorphic lens, dramatic chiaroscuro lighting, "
        "shallow depth of field, 35mm grain, desaturated color grade, award-winning cinematography"
    ),
    "watercolor":     (
        "soft watercolor illustration, loose expressive brushwork, paper texture, "
        "muted earthy palette, editorial art style, hand-painted feel"
    ),
    "digital_art":    (
        "vibrant digital concept art, highly detailed, ArtStation trending, "
        "dynamic composition, volumetric light, ultra-detailed environment"
    ),
    "photorealistic": (
        "professional DSLR photography, 85mm portrait lens, natural golden-hour lighting, "
        "tack-sharp foreground, bokeh background, editorial magazine quality"
    ),
    "comic":          (
        "graphic novel panel illustration, bold ink outlines, flat comic colors, "
        "dynamic action composition, expressive faces, Marvel/DC style"
    ),
    "corporate":      (
        "clean flat vector illustration, isometric 3D perspective, professional corporate style, "
        "minimal color palette of blues and greens, modern business aesthetic"
    ),
}

_NEGATIVE_PROMPT = (
    "no text, no watermarks, no logos, no borders, no low quality, "
    "no blurry, no distorted faces, no extra limbs"
)

class BasePromptEngineer(ABC):
    """
    Base class for prompt engineering. 
    Accepts a style parameter to pick lighting/look options.
    """
    def __init__(self, style: str = "cinematic"):
        self.style = style if style in STYLE_SUFFIXES else "cinematic"

    @abstractmethod
    def enhance(self, sentence: str, global_context: str = "", scene_index: int = 0, total_scenes: int = 1) -> str:
        """Return an enhanced visual prompt for the given sentence."""
        pass

    def negative_prompt(self) -> str:
        """Return the standard negative prompt string."""
        return _NEGATIVE_PROMPT
