"""
StoryForge — app.py
Flask application: orchestrates segmentation → prompt engineering → image generation → storyboard render.
"""

import os
import traceback
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from segmenter import segment_text
from prompt_engineers import get_prompt_engineer
from generators import get_generator

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB max request


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the input form."""
    styles = [
        {"id": "cinematic",    "label": "Cinematic",              "emoji": "🎬"},
        {"id": "watercolor",   "label": "Watercolor Illustration","emoji": "🎨"},
        {"id": "digital_art",  "label": "Digital Art",            "emoji": "💻"},
        {"id": "photorealistic","label": "Photorealistic",         "emoji": "📷"},
        {"id": "comic",        "label": "Comic Book",             "emoji": "💥"},
        {"id": "corporate",    "label": "Business Illustration",  "emoji": "📊"},
    ]
    providers = _available_providers()
    return render_template("index.html", styles=styles, providers=providers)


@app.route("/generate", methods=["POST"])
def generate():
    """
    Main pipeline endpoint.
    Accepts: text (str), style (str), provider (str), llm_enhance (bool)
    Returns: renders storyboard.html with generated panels
    """
    raw_text    = request.form.get("text", "").strip()
    style       = request.form.get("style", "cinematic")
    provider    = request.form.get("provider", "huggingface")
    llm_enhance = request.form.get("llm_enhance") == "on"

    # ── Validation ────────────────────────────────────────────────────────────
    if not raw_text:
        return render_template("index.html", error="Please provide a narrative text."), 400
    if len(raw_text) < 20:
        return render_template("index.html", error="Text is too short. Provide at least 3 sentences."), 400
    if len(raw_text) > 3000:
        return render_template("index.html", error="Text is too long. Keep it under 3,000 characters."), 400

    try:
        # ── Step 1: Segment text into scenes ──────────────────────────────────
        global_context, scenes = segment_text(raw_text, max_scenes=5, use_llm=llm_enhance)
        if len(scenes) < 2:
            return render_template(
                "index.html",
                error="Could not extract enough scenes. Try a longer narrative with 3–5 sentences."
            ), 400

        # ── Step 2: Engineer a visual prompt for each scene ───────────────────
        engineer = get_prompt_engineer(style=style, use_llm=llm_enhance)
        total_scenes = len(scenes)
        prompts = [
            engineer.enhance(scene, global_context, idx, total_scenes) 
            for idx, scene in enumerate(scenes)
        ]

        # ── Step 3: Generate an image for each prompt ─────────────────────────
        generator = get_generator(provider)
        panels    = []
        for idx, (scene, prompt) in enumerate(zip(scenes, prompts)):
            image_data = generator.generate(prompt, index=idx)
            panels.append({
                "number":    idx + 1,
                "caption":   scene,
                "prompt":    prompt,
                "image_url": image_data["url"],      # URL or data-URI
                "is_local":  image_data["is_local"],  # True = saved to /static/output/
            })

        # ── Step 4: Render storyboard ──────────────────────────────────────────
        return render_template(
            "storyboard.html",
            panels=panels,
            style=style,
            provider=provider,
            original_text=raw_text,
        )

    except ValueError as ve:
        return render_template("index.html", error=str(ve)), 400
    except Exception:
        app.logger.error(traceback.format_exc())
        return render_template(
            "index.html",
            error="An unexpected error occurred. Check your API keys and try again."
        ), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "providers": _available_providers()})


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _available_providers() -> list[dict]:
    """Return which image providers are configured."""
    return [
        {"id": "huggingface", "label": "FLUX.1-schnell", "available": bool(os.getenv("HF_TOKEN"))},
        {"id": "gemini",      "label": "Gemini 3.1 Flash Lite Preview", "available": bool(os.getenv("GEMINI_API_KEY"))},
        {"id": "stability",   "label": "Stable Diffusion 3.5", "available": bool(os.getenv("STABILITY_API_KEY"))},
        {"id": "stablehorde", "label": "Stable Diffusion (Stable Horde)", "available": True},
    ]


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
