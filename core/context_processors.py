from django.core.cache import cache

SIDEBAR_CACHE_KEY = "sidebar:v1"

def sidebar(request):
    data = cache.get(SIDEBAR_CACHE_KEY)
    if data is None:
        return {"popular_tags": [], "best_members": []}
    return data
