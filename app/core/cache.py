from cachetools import TTLCache

# caches
serp_cache = TTLCache(maxsize=1000, ttl=6*60*60)  # 6 hours
openrouter_cache = TTLCache(maxsize=1000, ttl=24*60*60)  # 24 hours
