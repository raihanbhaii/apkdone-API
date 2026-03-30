from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from aiocache import cached, Cache
import hashlib
import os
from scraper import get_app_detail, search_apps, get_final_direct_apk_url
from models import AppDetail, AppItem

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="APKDone Hidden Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

@app.get("/search")
@limiter.limit("30/minute")
@cached(ttl=1800, cache=Cache.REDIS, redis_url=REDIS_URL)
async def api_search(q: str = Query(..., min_length=2), page: int = 1, proxy: str = None):
    results = await search_apps(q, page, proxy)
    return {"results": results}

@app.get("/app")
@limiter.limit("20/minute")
@cached(ttl=3600, cache=Cache.REDIS, redis_url=REDIS_URL)
async def api_detail(url: str, proxy: str = None):
    if not url.startswith("https://apkdone.com/"):
        raise HTTPException(400, "Only apkdone.com URLs allowed")
    
    detail: AppDetail = await get_app_detail(url, proxy)
    
    # Generate clean hidden download links
    slug = detail.slug or hashlib.md5(url.encode()).hexdigest()[:12]
    for i, link in enumerate(detail.download_links):
        clean_id = f"{slug}-{i+1}"
        # Store mapping in Redis: clean_id → original apkdone download page URL
        await Cache(redis_url=REDIS_URL).set(f"dl:{clean_id}", link.original_url, ttl=3600)
        link.clean_url = f"/d/{clean_id}"
    
    return detail

@app.get("/d/{download_id}")
@limiter.limit("15/minute")
async def clean_hidden_download(download_id: str, proxy: str = None):
    """Clean URL - original apkdone.com is completely hidden"""
    cache = Cache(redis_url=REDIS_URL)
    original_url = await cache.get(f"dl:{download_id}")
    
    if not original_url:
        raise HTTPException(404, "Download link expired or invalid")
    
    direct_apk = await get_final_direct_apk_url(original_url, proxy)
    if not direct_apk:
        raise HTTPException(404, "Could not extract direct APK link")
    
    return RedirectResponse(url=direct_apk, status_code=302)

@app.get("/")
async def root():
    return {"status": "APKDone Hidden Scraper API running", "example": "/d/whatsapp-mod-1"}
