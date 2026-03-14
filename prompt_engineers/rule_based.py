import re
from .base import BasePromptEngineer, STYLE_SUFFIXES

# Rule-based: subject keywords → visual descriptors
_KEYWORD_ENRICHMENTS: list[tuple[str, str]] = [
    (r"\b(team|employee|staff|worker|colleague)\b",
     "a diverse group of focused professionals collaborating"),
    (r"\b(startup|company|business|firm|organization)\b",
     "a modern glass-walled office building with dynamic energy"),
    (r"\b(error|mistake|problem|chaos|struggle|drowning)\b",
     "a overwhelmed person surrounded by cascading papers and red warning screens"),
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
    Fast rule-based string replacements and simple style suffix appending.
    """

    def enhance(self, sentence: str, global_context: str = "", scene_index: int = 0, total_scenes: int = 1) -> str:
        """
        1. Inject global context string.
        2. Apply keyword enrichments to inject visual language
        3. Append composition and lighting descriptors
        4. Append style suffix
        """
        base = sentence.strip().rstrip(".")
        base = self._apply_enrichments(base)

        composition = (
            "wide establishing shot, rule-of-thirds composition, "
            "professional color grading, high visual impact"
        )
        style_suffix = STYLE_SUFFIXES[self.style]

        if global_context:
            return f"[{global_context}] {base}. {composition}. {style_suffix}."
        return f"{base}. {composition}. {style_suffix}."

    def _apply_enrichments(self, text: str) -> str:
        """
        Scan for domain keywords and prepend/inject a richer visual descriptor.
        Only the first matching keyword enrichment is applied to avoid clutter.
        """
        lowered = text.lower()
        for pattern, enrichment in _KEYWORD_ENRICHMENTS:
            if re.search(pattern, lowered, re.IGNORECASE):
                # Inject enrichment as a parenthetical visual note
                return f"{text} — visualised as {enrichment}"
        return text
