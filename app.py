"""
StoryForge — app.py
Flask application: orchestrates segmentation → prompt engineering → image generation → storyboard render.
"""

import os
import traceback
import threading
import uuid
import time
import json
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv

from segmenter import segment_text
from prompt_engineers import get_prompt_engineer
from generators import get_generator

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB max request

# In-memory task tracker for SSE status streaming
_tasks = {}


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the input form."""
    styles = [
        {"id": "cinematic_film_noir",     "label": "Cinematic Film Noir",    "emoji": "🎬"},
        {"id": "cyberpunk_neon",          "label": "Cyberpunk Neon",         "emoji": "🏙️"},
        {"id": "vintage_sketchbook",      "label": "Vintage Sketchbook",     "emoji": "📒"},
        {"id": "studio_ghibli_watercolor","label": "Ghibli Watercolor",      "emoji": "🎨"},
        {"id": "high_fashion_editorial",  "label": "Editorial High Fashion", "emoji": "👗"},
        {"id": "editorial_photography",   "label": "Editorial Photography",  "emoji": "📷"},
        {"id": "graphic_novel_ink",       "label": "Graphic Novel Ink",      "emoji": "🖋️"},
    ]
    providers = _available_providers()
    return render_template("index.html", styles=styles, providers=providers)


@app.route("/generate", methods=["POST"])
def generate():
    """
    Kicks off the pipeline in a background thread and returns a task_id for tracking.
    """
    raw_text    = request.form.get("text", "").strip()
    style       = request.form.get("style", "cinematic")
    provider    = request.form.get("provider", "huggingface")
    llm_enhance = request.form.get("llm_enhance") == "on"

    if not raw_text or len(raw_text) < 20:
        return jsonify({"error": "Text is too short. Provide at least 3 sentences."}), 400
    if len(raw_text) > 3000:
        return jsonify({"error": "Text is too long. Keep it under 3,000 characters."}), 400

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "status": "initializing",
        "message": "Initializing pipeline...",
        "result": None,
        "error": None
    }

    # Start background thread
    t = threading.Thread(target=_run_pipeline, args=(task_id, raw_text, style, provider, llm_enhance))
    t.start()

    return jsonify({"task_id": task_id})


def _run_pipeline(task_id: str, raw_text: str, style: str, provider: str, llm_enhance: bool):
    try:
        task = _tasks[task_id]
        
        # ── Step 1: Segment text into scenes ──────────────────────────────────
        task["status"] = "segmenting"
        task["message"] = "SEGMENTING NARRATIVE... [IN PROGRESS]"
        
        global_context, scenes = segment_text(raw_text, max_scenes=6, use_llm=llm_enhance)
        if len(scenes) < 2:
            raise ValueError("Could not extract enough scenes. Try a longer narrative with 3–5 sentences.")

        task["message"] = f"SEGMENTING NARRATIVE... [OK] ({len(scenes)} scenes found)"
        time.sleep(0.1)

        # ── Step 2: Engineer a visual prompt for each scene ───────────────────
        task["status"] = "prompting"
        task["message"] = "ENGINEERING PROMPTS... [IN PROGRESS]"
        
        engineer = get_prompt_engineer(style=style, use_llm=llm_enhance)
        total_scenes = len(scenes)
        prompts = [
            engineer.enhance(scene, global_context, idx, total_scenes) 
            for idx, scene in enumerate(scenes)
        ]

        task["message"] = "ENGINEERING PROMPTS... [OK]"
        time.sleep(0.1)

        # ── Step 3: Generate an image for each prompt ─────────────────────────
        task["status"] = "generating"
        generator = get_generator(provider)
        panels    = []
        
        for idx, (scene, prompt) in enumerate(zip(scenes, prompts)):
            task["message"] = f"GENERATING HIGH-FI IMAGES... (Panel {idx + 1}/{total_scenes})"
            image_data = generator.generate(prompt, index=idx)
            panels.append({
                "number":    idx + 1,
                "caption":   scene,
                "prompt":    prompt,
                "image_url": image_data["url"],      
                "is_local":  image_data["is_local"],  
            })

        # ── Step 4: Render storyboard ──────────────────────────────────────────
        task["status"] = "rendering"
        task["message"] = "COMPILING STORYBOARD..."
        
        # Render the HTML directly so the frontend can inject it
        with app.test_request_context():
            final_html = render_template(
                "storyboard.html",
                panels=panels,
                style=style,
                provider=provider,
                narrative=raw_text,
            )
            
        task["result"] = final_html
        task["status"] = "complete"

    except ValueError as ve:
        task["status"] = "error"
        task["error"] = str(ve)
    except Exception as e:
        app.logger.error(traceback.format_exc())
        task["status"] = "error"
        # Extract a clean-ish error message from the exception
        task["error"] = f"System Error: {str(e)}"


@app.route("/stream/<task_id>")
def stream(task_id):
    """
    Server-Sent Events endpoint to yield live update status to the frontend.
    """
    def generate_events():
        last_status = None
        last_message = None
        
        while True:
            if task_id not in _tasks:
                yield f"data: {json.dumps({'status': 'error', 'error': 'Task not found'})}\n\n"
                break
                
            task = _tasks[task_id]
            
            # Only send if state changed to avoid spam
            if task["status"] != last_status or task["message"] != last_message:
                last_status = task["status"]
                last_message = task["message"]
                
                payload = {
                    "status": task["status"],
                    "message": task["message"],
                }
                
                if task["status"] == "complete":
                    payload["html"] = task["result"]
                    yield f"data: {json.dumps(payload)}\n\n"
                    break
                    
                if task["status"] == "error":
                    payload["error"] = task["error"]
                    yield f"data: {json.dumps(payload)}\n\n"
                    break
                    
                yield f"data: {json.dumps(payload)}\n\n"
                
            time.sleep(0.5)

    return Response(generate_events(), mimetype="text/event-stream")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "providers": _available_providers()})


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _available_providers() -> list[dict]:
    """Return which image providers are configured."""
    return [
        {"id": "gemini",      "label": "Google Gemini (Dynamic)", "available": bool(os.getenv("GEMINI_API_KEY"))},
        {"id": "huggingface", "label": "Hugging Face (Pro)", "available": bool(os.getenv("HF_TOKEN"))},
        {"id": "stability",   "label": "Stability AI (Pro)", "available": bool(os.getenv("STABILITY_API_KEY"))},
        {"id": "stablehorde", "label": "Stable Horde (Free)", "available": True},
    ]


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
