"""
prompt_engineers/rule_based.py
Fast, offline, deterministic prompt engineer.
Uses keyword enrichments + arc-aware compositions from base.py.
No API key required — always available as fallback.
"""

import re
from .base import (
    BasePromptEngineer,
    STYLE_SUFFIXES,
    PANEL_COMPOSITIONS,
    ARC_TONES,
    arc_slot,
)

# ─── Keyword → Visual Descriptor Map ─────────────────────────────────────────
# First matching keyword wins — only one enrichment applied per sentence
# to avoid prompt clutter.

_KEYWORD_ENRICHMENTS: list[tuple[str, str]] = [
    (r"\b(team|employee|staff|worker|colleague)\b",
     "a diverse group of focused professionals collaborating"),
    (r"\b(startup|company|business|firm|organization)\b",
     "a modern glass-walled office building with dynamic energy"),
    (r"\b(error|mistake|problem|chaos|struggle|drowning)\b",
     "an overwhelmed person surrounded by cascading papers and red warning screens"),
    (r"\b(platform|software|app|tool|system|AI|technology)\b",
     "a sleek holographic dashboard glowing with data streams and clean UI"),
    (r"\b(growth|scale|expand|success|achieve|thrive)\b",
     "a confident figure standing before an ascending graph with city skyline backdrop"),
    (r"\b(data|analytics|insight|metric|dashboard)\b",
     "glowing analytical charts and real-time data visualizations on dark screens"),
    (r"\b(city|cities|global|world|international)\b",
     "an aerial panoramic view of a glittering metropolitan skyline at dusk"),
    (r"\b(money|dollar|revenue|profit|cost|saving)\b",
     "golden coins and upward-trending financial charts in a clean environment"),
    (r"\b(customer|client|user|person|people)\b",
     "smiling satisfied people interacting with elegant digital interfaces"),
    (r"\b(fast|speed|rapid|quick|instant|within)\b",
     "motion blur trails suggesting rapid transformation and momentum"),
]


class RuleBasedPromptEngineer(BasePromptEngineer):
    """
    Offline prompt engineer — no API calls, no latency.
    Uses keyword enrichment + arc-position-based compositions.
    Used as primary when use_llm=False and as fallback for GeminiPromptEngineer.
    """

    def enhance(
        self,
        sentence: str,
        global_context: str = "",
        scene_index: int = 0,
        total_scenes: int = 1,
    ) -> str:
        """
        Build prompt in 4 layers:
          1. Global context anchor
          2. Enriched scene sentence
          3. Arc-aware camera composition
          4. Style suffix
        """
        base = sentence.strip().rstrip(".")
        base = self._apply_enrichments(base)

        slot        = arc_slot(scene_index, total_scenes)
        composition = PANEL_COMPOSITIONS[slot]
        style_suffix = STYLE_SUFFIXES[self.style]

        if global_context:
            return (
                f"[{global_context}] "
                f"{base}. "
                f"{composition}. "
                f"{style_suffix}."
            )
        return f"{base}. {composition}. {style_suffix}."

    def _apply_enrichments(self, text: str) -> str:
        """
        Scan for domain keywords and inject a richer visual descriptor.
        Only the first matching enrichment is applied to avoid clutter.
        """
        lowered = text.lower()
        for pattern, enrichment in _KEYWORD_ENRICHMENTS:
            if re.search(pattern, lowered, re.IGNORECASE):
                return f"{text} — visualised as {enrichment}"
        return text
        