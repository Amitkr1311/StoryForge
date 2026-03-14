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
        "You are an expert storyboard artist and script supervisor. "
        "Analyze the provided narrative paragraph and produce JSON output with two keys:\n\n"
        "1. 'global_context': A single concise string describing the unified visual constants "
        "(the specific industry, physical setting, core subjects, and visual mood). "
        "This will anchor every image prompt so they look like they belong to the same world.\n"
        "2. 'scenes': A list of purely semantic story beats (action/state descriptions). "
        "Split the narrative into distinct visual moments (minimum 2, maximum 5). "
        "Rewrite nouns into each scene (e.g., turn 'They' into 'The team of engineers') "
        "so each scene is completely self-contained and visually literal."
    )

    user_msg = f"Narrative text to parse up to {max_scenes} panels max:\n\"{text}\""

    # Use JSON schema constrained output for reliable parsing
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
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
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["global_context", "scenes"]
            }
        )
    )

    data = json.loads(response.text)
    context = data.get("global_context", "")
    scenes  = data.get("scenes", [])

    # Enforcement clamping if LLM hallucinated too many list items
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

