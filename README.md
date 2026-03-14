# StoryForge

Turn plain business narratives into beautiful, cohesive 3-5 panel visual storyboards instantly.

StoryForge uses AI specifically tuned for narrative arc extraction, consistent prompt framing, and literal scene generation to help founders, writers, and marketers visualize their pitches without hallucination or style drift.

## Table of Contents
- [Features](#features)
- [Architecture & Pipeline](#architecture--pipeline)
- [Prompt Engineering Methodology](#prompt-engineering-methodology)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)

## Features
- **Dynamic Storyboard Generation**: Automatically extracts 3 to 5 scenes from raw text.
- **Context Consistency**: Extracts "Global Context" (industry, setting, subjects) to anchor visual generation across all panels.
- **Emotional Arc Mapping**: Adjusts lighting and mood based on the scene's chronological position (e.g., tense openings, triumphant conclusions).
- **Multiple Image Engines**: Supports HuggingFace (Flux.1), Stable Horde, Stability AI, and Gemini.
- **Stitch Design System**: Beautiful asymmetrical magazine-layout UI optimized for pitch presentations.

---

## Architecture & Pipeline
The application runs on a modular Flask backend. When a user submits a corporate narrative, it flows through a sequential, anti-hallucination pipeline:

1. **Input Validation (`app.py`)**: Checks for length constraints and sanitizes text.
2. **Global & Semantic Extraction (`segmenter.py`)**:
   - Sends the raw narrative to an LLM (Gemini 3.1 Flash Lite) running in strict JSON constraint mode.
   - Extracts a `global_context` string (e.g., "A bright logistics warehouse").
   - Resolves pronouns and splits the story into 3-5 distinct visual "beats".
3. **Prompt Anchoring (`prompt_engineers/gemini.py`)**:
   - The LLM constructs a 3-layer prompt: 
     1. The literal action beat.
     2. The shared `global_context` anchor.
     3. The user's active style preference.
4. **Image Synthesis (`generators/`)**: 
   - A highly modular factory sends the anchored prompts to the chosen provider (HuggingFace, Stability, etc.) via asynchronous REST requests.
5. **Layout Rendering (`storyboard.html`)**:
   - Jinja iterates over the returned image binaries, rendering them in a responsive, dynamic masonry grid natively styled with pure brutalist CSS.

---

## Prompt Engineering Methodology

Our prompt pipeline is designed to eliminate the two biggest issues with AI storyboarding: **Style Drift** and **Subject Hallucination**. 

### 1. Anchored Context (Layered Build)
We decouple the "action" from the "environment." By extracting the global environment *first* and appending it manually to every single prompt, the image model is mathematically forced to render the exact same warehouse and characters in Panel 5 as it did in Panel 1.

### 2. Low-Temperature Literal Translation
When `gemini.py` writes the final image generation prompt, it runs at `temperature=0.35`. We explicitly instruct it in the System Prompt to act as a *literal visual translator*, strictly forbidding it from inventing background characters, props, or scenes not explicitly mentioned in the original text.

### 3. Chronological Emotional Arcs
We calculate `scene_index / total_scenes`.
- **Opening Panels**: Injected with descriptors like *"tense, heavy, representing a real visible problem"*.
- **Middle Panels**: Injected with *"transitional, effort, momentum"*.
- **Closing Panels**: Injected with *"resolved, expansive, successful"*.
This ensures the visual lighting tells a story even if the user's text is dry.

---

## Setup & Installation

### 1. Clone & Environment
```bash
git clone https://github.com/yourusername/storyforge.git
cd storyforge
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Key Management
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and fill out your keys:
- `GEMINI_API_KEY`: Required for LLM Context Extraction and Prompt Engineering (Free Tier available).
- `HF_TOKEN`: Required for HuggingFace fast image generation.
- `STABILITY_API_KEY`: Optional, required only if using Stable Diffusion 3.5.

### 3. Execution
Run the development server natively:
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5000`.

## Usage
1. Type a corporate narrative or business pitch into the input box (minimum 3 sentences).
2. Select your visual style (e.g., Cinematic, Digital Art).
3. Select an Image Engine.
4. Toggle "SUPERCHARGE PROMPTS (Gemini Flash)" to enable the anti-hallucination context extraction.
5. Click **Visualize Pitch** and wait 5–15 seconds for your storyboard!
