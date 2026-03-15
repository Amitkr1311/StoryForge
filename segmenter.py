"""
segmenter.py
Extracts unified global context and semantic scenes from raw narrative text.

If an LLM API key (GEMINI_API_KEY) is available, uses Gemini 3.1 Flash Lite 
to cleanly separate story beats and extract setting/subject constants.
Otherwise, falls back to grammar-based sentence splitting.
"""

import os
import re
import json

# ── NLTK ──────────────────────────────────────────────────────────────────────
try:
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    from nltk.tokenize import sent_tokenize as _nltk_tokenize
    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False

# ── spaCy (optional upgrade) ──────────────────────────────────────────────────
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
    _SPACY_AVAILABLE = True
except Exception:
    _SPACY_AVAILABLE = False


# ─── Public API ───────────────────────────────────────────────────────────────

def segment_text(text: str, max_scenes: int = 5, backend: str = "auto", use_llm: bool = False) -> tuple[str, list[str]]:
    """
    Tokenize `text` into a global context string and story scenes.

    Args:
        text:       Raw user narrative (may contain multiple paragraphs).
        max_scenes: Upper bound on panel count. Min is always 3.
        backend:    "nltk" | "spacy" | "auto"  (auto prefers spaCy if available)
        use_llm:    If True, attempts to use Gemini to extract context and beats.

    Returns:
        tuple(global_context_str, list_of_scenes)
    """
    text = _clean(text)
    api_key = os.getenv("GEMINI_API_KEY")

    if use_llm and api_key:
        try:
            return _llm_segment(text, max_scenes, api_key)
        except Exception as e:
            pass

    # ── Fallback tokenisation backend ─────────────────────────────────────────
    if backend == "spacy" or (backend == "auto" and _SPACY_AVAILABLE):
        sentences = _spacy_tokenize(text)
    elif backend == "nltk" or (backend == "auto" and _NLTK_AVAILABLE):
        sentences = _nltk_tokenize(text)
    else:
        # Pure-Python fallback: split on . ! ?
        sentences = _regex_tokenize(text)

    # Merge short fragments and clamp
    sentences = _merge_short(sentences, min_words=6)
    sentences = _clamp(sentences, max_scenes)

    # Empty context string on fallback
    return "", sentences


# ─── Data Extraction ──────────────────────────────────────────────────────────

def _llm_segment(text: str, max_scenes: int, api_key: str) -> tuple[str, list[str]]:
    """
    Uses Gemini 3.1 Flash Lite to parse the raw text into global context
    and semantic story beats instead of pure grammatical sentences.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    system_msg = (
    "You are an expert storyboard supervisor preparing a visual shooting script. "
    "Your output must be strictly valid JSON with exactly two keys: "
    "'global_context' and 'scenes'. No markdown, no code fences, no commentary — "
    "raw JSON only.\n\n"

    "KEY 1 — 'global_context' (string):\n"
    "Write a single grounding sentence of 20–35 words that locks in the visual world "
    "shared by ALL panels. It must specify:\n"
    "  - The exact physical setting (e.g. 'a cluttered warehouse office with fluorescent lighting')\n"
    "  - Who the subjects are (e.g. 'a team of three exhausted logistics workers')\n"
    "  - The industry or domain (e.g. 'small logistics startup')\n"
    "  - One recurring visual element that ties the panels together "
    "(e.g. 'spreadsheet-covered monitors')\n"
    "Do NOT include emotional language, plot summary, or abstract concepts.\n\n"

    "KEY 2 — 'scenes' (array of strings, minimum 2, maximum 5):\n"
    "Split the narrative into distinct visual moments — each one a single thing "
    "a camera could capture in a still frame.\n"
    "Rules for each scene string:\n"
    "  - Replace ALL pronouns with their specific referents "
    "(e.g. 'They' → 'The three logistics workers', 'it' → 'the inventory spreadsheet')\n"
    "  - Write in simple present tense, active voice "
    "(e.g. 'The manager stares at a screen full of red error flags')\n"
    "  - Describe only what is LITERALLY VISIBLE — no emotions, no implications, "
    "no future states, no abstract ideas\n"
    "  - Each scene must make visual sense without reading any other scene\n"
    "  - Maximum 25 words per scene\n\n"

    "SPLIT LOGIC — where to cut scenes:\n"
    "  - Cut when the physical location changes\n"
    "  - Cut when the emotional state visibly shifts\n"
    "  - Cut when a new object or person becomes the focus\n"
    "  - Do NOT cut mid-action or mid-sentence if the visual hasn't changed\n\n"

    "The arc across scenes should move from PROBLEM → STRUGGLE → TURNING POINT → RESOLUTION. "
    "If the narrative has fewer than 4 beats, collapse adjacent similar states.\n\n"

    "Output format (follow exactly):\n"
    '{"global_context": "...", "scenes": ["...", "...", "..."]}'
)

    user_msg = f"Narrative text to parse up to {max_scenes} panels max:\n\"{text}\""

    try:
        # Use JSON schema constrained output for reliable parsing
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system_msg,
                temperature=0.2, # Very literal constraint
                response_mime_type="application/json",
                response_schema={

                "type": "OBJECT",
                "properties": {
                    "global_context": {"type": "STRING"},
                    "scenes": {
                        "type": "ARRAY",
                        "minItems": 2,
                        "maxItems": 5,
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["global_context", "scenes"]
            }
        )
    )
    except Exception as e:
        raise ValueError(f"Gemini API call failed during segmentation: {e}")

    try:
        return _parse_segmentation_response(response.text, max_scenes=max_scenes, min_scenes=2)
    except ValueError as e:
        raise


def _parse_segmentation_response(
    response_text: str,
    max_scenes: int = 5,
    min_scenes: int = 2
) -> tuple[str, list[str]]:
    
    # ── 1. Parse JSON safely ───────────────────────────────────
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}")

    # ── 2. Extract with fallbacks ──────────────────────────────
    context = data.get("global_context", "").strip()
    scenes  = data.get("scenes", [])

    # ── 3. Validate global_context ────────────────────────────
    if not context:
        raise ValueError(
            "Gemini returned an empty global_context. "
            "Try rephrasing your narrative."
        )

    # ── 4. Validate scenes is actually a list ─────────────────
    if not isinstance(scenes, list):
        raise ValueError(
            f"Expected 'scenes' to be a list, got {type(scenes).__name__}."
        )

    # ── 5. Clean individual scenes ────────────────────────────
    scenes = [s.strip() for s in scenes if isinstance(s, str) and s.strip()]

    # ── 6. Remove near-duplicates ─────────────────────────────
    seen   = set()
    unique = []
    for scene in scenes:
        key = scene[:40].lower()   # compare first 40 chars
        if key not in seen:
            seen.add(key)
            unique.append(scene)
    scenes = unique

    # ── 7. Enforce min / max bounds ───────────────────────────
    if len(scenes) < min_scenes:
        raise ValueError(
            f"Only {len(scenes)} usable scene(s) extracted — "
            f"need at least {min_scenes}. Try a longer narrative."
        )

    if len(scenes) > max_scenes:
        scenes = _clamp(scenes, max_scenes)

    return context, scenes



# ─── Fallback Tokenisers ──────────────────────────────────────────────────────

def _spacy_tokenize(text: str) -> list[str]:
    doc = _nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

def _regex_tokenize(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if s.strip()]


# ─── Post-processing helpers ──────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def _merge_short(sentences: list[str], min_words: int = 6) -> list[str]:
    if not sentences:
        return sentences
    merged = [sentences[0]]
    for sent in sentences[1:]:
        if len(sent.split()) < min_words:
            merged[-1] = merged[-1].rstrip(".!?") + ". " + sent
        else:
            merged.append(sent)
    return merged

def _clamp(sentences: list[str], max_scenes: int) -> list[str]:
    while len(sentences) > max_scenes:
        min_len  = float("inf")
        merge_at = 0
        for i in range(len(sentences) - 1):
            pair_len = len(sentences[i]) + len(sentences[i + 1])
            if pair_len < min_len:
                min_len  = pair_len
                merge_at = i

        combined = sentences[merge_at].rstrip(" ") + " " + sentences[merge_at + 1]
        sentences = sentences[:merge_at] + [combined] + sentences[merge_at + 2:]
    return sentences

