import requests
from app.core.config import settings
from app.core.cache import openrouter_cache
import json

class IAService:
    def __init__(self):
        self.key = settings.OPENROUTER_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base = "https://api.openrouter.ai/v1"

    def chat(self, prompt: str):
        cache_key = f"open:{hash(prompt)}"
        if cache_key in openrouter_cache:
            return openrouter_cache[cache_key]
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500}
        resp = requests.post(f"{self.base}/chat/completions", headers=headers, json=body, timeout=20)
        text = resp.text
        try:
            j = resp.json()
        except Exception:
            raise ValueError("IA did not return valid JSON")
        # ensure JSON only (no markdown)
        res_text = j
        openrouter_cache[cache_key] = res_text
        return res_text
