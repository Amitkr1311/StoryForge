"""
Stable Horde — Free community-powered Stable Diffusion

Anonymous key '0000000000' works without sign-up.
Create a free account at https://stablehorde.net for higher priority.
Set STABLE_HORDE_KEY in your .env file.

No extra packages — uses only built-in urllib + json.
"""

import os
import json
import time
import urllib.request
import urllib.error

from generators.base import BaseImageGenerator


class StableHordeGenerator(BaseImageGenerator):
    """Community-run distributed Stable Diffusion inference — always free."""

    _API_BASE = "https://stablehorde.net/api/v2"

    def generate(self, prompt: str, index: int = 0) -> dict:
        api_key = os.getenv("STABLE_HORDE_KEY", "0000000000")
        masked  = api_key[:8] + "..." if len(api_key) > 8 else api_key
        print(f"\n[StableHorde] Panel {index} — using key: '{masked}'")
        print(f"[StableHorde] Prompt ({len(prompt)} chars): {prompt[:120]}...")

        headers = {
            "Content-Type": "application/json",
            "apikey": api_key,
            "Client-Agent": "PitchVisualizer:1.0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        payload = json.dumps({
            "prompt": prompt[:1000],
            "params": {
                "width":        640,
                "height":       384,
                "steps":        20,
                "cfg_scale":    7,
                "sampler_name": "k_euler",
                "n":            1,
            },
            "models": ["stable_diffusion"],
            "nsfw":   False,
            "r2":     True,
        }).encode()

        # ── Step 1: Submit job ────────────────────────────────────────────────
        submit_url = f"{self._API_BASE}/generate/async"
        print(f"[StableHorde] POST {submit_url}")
        req = urllib.request.Request(submit_url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                job  = json.loads(body)
                print(f"[StableHorde] Submit response: {body[:300]}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            print(f"[StableHorde] HTTP {exc.code} {exc.reason} — body: {body[:500]}")
            raise ValueError(f"Stable Horde: HTTP {exc.code} — {body[:200]}") from exc
        except Exception as exc:
            print(f"[StableHorde] Submit exception: {exc}")
            raise ValueError(f"Stable Horde submit failed: {exc}") from exc

        job_id = job.get("id")
        if not job_id:
            raise ValueError(f"Stable Horde returned no job ID: {job}")
        print(f"[StableHorde] Job ID: {job_id}")

        # ── Step 2: Poll until done (max ~3 min) ─────────────────────────────
        check_url = f"{self._API_BASE}/generate/check/{job_id}"
        for poll_n in range(36):
            time.sleep(5)
            try:
                with urllib.request.urlopen(check_url, timeout=15) as resp:
                    status = json.loads(resp.read())
                    print(f"[StableHorde] Poll #{poll_n+1}: done={status.get('done')} "
                          f"wait={status.get('wait_time')}s queue={status.get('queue_position')}")
            except Exception as e:
                print(f"[StableHorde] Poll error (retrying): {e}")
                continue
            if status.get("done"):
                break
        else:
            raise ValueError("Stable Horde timed out after 3 minutes.")

        # ── Step 3: Fetch result ──────────────────────────────────────────────
        status_url = f"{self._API_BASE}/generate/status/{job_id}"
        print(f"[StableHorde] Fetching result from {status_url}")
        with urllib.request.urlopen(status_url, timeout=30) as resp:
            result = json.loads(resp.read())

        generations = result.get("generations", [])
        if not generations:
            raise ValueError(f"Stable Horde returned no images: {result}")

        img_url = generations[0].get("img")
        print(f"[StableHorde] Image URL: {img_url}")
        if not img_url:
            raise ValueError("Stable Horde generation missing image URL.")

        # ── Step 4: Download image ────────────────────────────────────────────
        with urllib.request.urlopen(img_url, timeout=30) as resp:
            image_bytes = resp.read()
        print(f"[StableHorde] Downloaded {len(image_bytes)} bytes — saving...")

        local_path = self._save_image_bytes(image_bytes, suffix="webp")
        print(f"[StableHorde] Saved to {local_path}")
        return {"url": local_path, "is_local": True}
