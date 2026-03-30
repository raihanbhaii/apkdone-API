from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import hashlib
from functools import lru_cache
import asyncio

from scraper import get_app_detail, search_apps
from models import AppDetail

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="APKDone API - Free Tier (No Redis)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory cache
download_cache = {}

@app.get("/search")
@limiter.limit("15/minute")
async def api_search(q: str = Query(..., min_length=2), page: int = 1):
    results = await search_apps(q, page)
    return {"query": q, "results": results}

@app.get("/app")
@limiter.limit("10/minute")
async def api_detail(url: str):
    if not url.startswith("https://apkdone.com/"):
        raise HTTPException(400, "Only apkdone.com URLs allowed")
    
    detail: AppDetail = await get_app_detail(url)
    
    # Generate clean hidden download URLs
    slug = detail.slug or hashlib.md5(url.encode()).hexdigest()[:12]
    
    for i, link in enumerate(detail.download_links):
        clean_id = f"{slug}-{i+1}"
        # Store in memory (will be lost on restart)
        download_cache[clean_id] = link.original_url
        link.clean_url = f"/d/{clean_id}"
    
    return detail

@app.get("/d/{download_id}")
@limiter.limit("8/minute")
async def clean_hidden_download(download_id: str):
    """Clean URL - apkdone.com is completely hidden"""
    original_url = download_cache.get(download_id)
    
    if not original_url:
        raise HTTPException(404, "Download link expired or invalid. Try getting app details again.")
    
    # Redirect to the download page (best we can do reliably on free tier)
    return RedirectResponse(url=original_url, status_code=302)

@app.get("/")
async def root():
    return {
        "status": "✅ API is running on Render Free Tier",
        "usage": "1. GET /app?url=https://apkdone.com/app-name/",
        "note": "Use the 'clean_url' from response for hidden downloads"
    }
