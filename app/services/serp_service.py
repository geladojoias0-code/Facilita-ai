import requests
from app.core.config import settings
from app.core.cache import serp_cache
from app.utils.constants import SERP_IGNORED_SCHEDULES

class SerpService:
    def __init__(self):
        self.key = settings.SERPAPI_KEY
        self.location = settings.SERP_LL

    def buscar(self, query: str, limit: int = 20):
        cache_key = f"serp:{query}:{limit}"
        if cache_key in serp_cache:
            return serp_cache[cache_key]
        params = {"engine": "google_maps", "type": "search", "q": query, "google_domain": "google.com.br", "location": self.location, "api_key": self.key}
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        data = resp.json()
        results = []
        for r in data.get('local_results', [])[:limit]:
            phone = r.get('phone')
            rating = float(r.get('rating', 0)) if r.get('rating') else 0
            reviews = int(r.get('reviews', 0)) if r.get('reviews') else 0
            title = r.get('title','')
            if rating >= 4.8 and 4 <= reviews <= 45 and phone:
                lower = title.lower()
                if any(k in lower for k in SERP_IGNORED_SCHEDULES):
                    continue
                results.append({"place_id": r.get('place_id'),"nome": title,"whatsapp": phone,"link_maps": r.get('link'),"avaliacoes": reviews,"score": rating})
        serp_cache[cache_key] = results
        return results
