from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer
import os
import hashlib

from scraper import get_app_detail, search_apps
from models import AppDetail

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="APKDone API - Free Tier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL")

# Create cache instance properly
cache = Cache(
    Cache.REDIS,
    endpoint=REDIS_URL.replace("redis://", "").split(":")[0] if REDIS_URL else "localhost",
    port=6379,
    serializer=JsonSerializer(),
    namespace="apkdone"
) if REDIS_URL else Cache(Cache.MEMORY)

@app.get("/search")
@limiter.limit("20/minute")
@cached(ttl=1800, cache=cache, key_builder=lambda *args, **kwargs: f"search:{kwargs.get('q')}")
async def api_search(q: str = Query(..., min_length=2), page: int = 1):
    results = await search_apps(q, page)
    return {"results": results}

@app.get("/app")
@limiter.limit("15/minute")
@cached(ttl=3600, cache=cache)
async def api_detail(url: str):
    if not url.startswith("https://apkdone.com/"):
        raise HTTPException(400, "Only apkdone.com URLs allowed")
    
    detail: AppDetail = await get_app_detail(url)
    
    slug = detail.slug or hashlib.md5(url.encode()).hexdigest()[:12]
    for i, link in enumerate(detail.download_links):
        clean_id = f"{slug}-{i+1}"
        await cache.set(f"dl:{clean_id}", link.original_url, ttl=3600)
        link.clean_url = f"/d/{clean_id}"
    
    return detail

@app.get("/d/{download_id}")
@limiter.limit("10/minute")
async def clean_hidden_download(download_id: str):
    original_url = await cache.get(f"dl:{download_id}")
    if not original_url:
        raise HTTPException(404, "Download link expired or invalid")
    
    # On free tier we redirect to the download page (best we can do reliably)
    return RedirectResponse(url=original_url, status_code=302)

@app.get("/")
async def root():
    return {"status": "✅ API running on Render Free", "note": "Use /app?url=... then click clean_url"}
