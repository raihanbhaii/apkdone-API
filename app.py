import re
import hashlib
from urllib.parse import urljoin, quote_plus
from typing import List, Optional, Dict, Any

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

# ─── Models ───────────────────────────────────────────────────────────────────

class DownloadLink(BaseModel):
    name: str
    original_url: str
    clean_url: Optional[str] = None

class AppDetail(BaseModel):
    title: str
    slug: str
    url: str
    logo: Optional[str] = None
    version: str
    size: Optional[str] = None
    updated: Optional[str] = None
    requires_android: Optional[str] = None
    description: str = ""
    download_links: List[DownloadLink] = []

class AppItem(BaseModel):
    title: str
    url: str
    image: Optional[str] = None
    category: Optional[str] = None

class CategoryItem(BaseModel):
    name: str
    url: str
    slug: str

class TrendingApp(BaseModel):
    title: str
    url: str
    image: Optional[str] = None
    rank: Optional[int] = None

# ─── Config ───────────────────────────────────────────────────────────────────

BASE_URL = "https://apkdone.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/134.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

download_cache: dict[str, str] = {}

# ─── App Setup ────────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="APKDone API", description="Free-tier APKDone scraper", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Helpers ──────────────────────────────────────────────────────────────────

async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text

def get_img(tag) -> Optional[str]:
    if not tag:
        return None
    src = tag.get("data-src") or tag.get("src") or ""
    return urljoin(BASE_URL, src) if src else None

def parse_app_items(soup: BeautifulSoup, selector: str, limit: int = 12, category: str = None) -> List[AppItem]:
    apps, seen = [], set()
    for item in soup.select(selector)[:limit]:
        a = item.select_one("h2 a, h3 a, .title a, a[href]")
        if not a:
            continue
        href = urljoin(BASE_URL, a.get("href", ""))
        if href in seen:
            continue
        seen.add(href)
        apps.append(AppItem(
            title=a.get_text(strip=True) or "Unknown",
            url=href,
            image=get_img(item.select_one("img")),
            category=category,
        ))
    return apps

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "✅ APKDone API running (Render Free Tier)",
        "endpoints": {
            "home":       "GET /home",
            "trending":   "GET /trending",
            "games":      "GET /games?page=1",
            "categories": "GET /categories",
            "category":   "GET /category/{slug}?page=1",
            "search":     "GET /search?q=minecraft&page=1",
            "app_detail": "GET /app?url=https://apkdone.com/app-name/",
            "download":   "GET /d/{download_id}",
        },
    }


@app.get("/home")
@limiter.limit("10/minute")
async def homepage(request: Request):
    html = await fetch_html(BASE_URL)
    soup = BeautifulSoup(html, "lxml")
    selector = "article, .post-item, .app-item"
    all_apps = parse_app_items(soup, selector, limit=30)
    return {
        "featured": all_apps[:8],
        "new_apps": all_apps[8:18],
        "popular":  all_apps[18:28],
    }


@app.get("/trending")
@limiter.limit("10/minute")
async def trending(request: Request, page: int = Query(1, ge=1)):
    for url in [f"{BASE_URL}/trending/", f"{BASE_URL}/popular/", BASE_URL]:
        try:
            html = await fetch_html(url)
            break
        except Exception:
            html = None
    if not html:
        return {"page": page, "results": []}
    soup = BeautifulSoup(html, "lxml")
    items = parse_app_items(soup, "article, .post-item", limit=20)
    results = [TrendingApp(title=a.title, url=a.url, image=a.image, rank=i+1) for i, a in enumerate(items)]
    return {"page": page, "results": results}


@app.get("/games")
@limiter.limit("10/minute")
async def games(request: Request, page: int = Query(1, ge=1)):
    url = f"{BASE_URL}/category/games/" if page == 1 else f"{BASE_URL}/category/games/page/{page}/"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    results = parse_app_items(soup, "article, .post-item", limit=20, category="games")
    return {"page": page, "category": "games", "results": results}


@app.get("/categories")
@limiter.limit("10/minute")
async def categories(request: Request):
    html = await fetch_html(BASE_URL)
    soup = BeautifulSoup(html, "lxml")
    cats, seen = [], set()
    for a in soup.select("nav a, .categories a, .widget_categories a, .menu-item a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if not href or not text:
            continue
        full_url = urljoin(BASE_URL, href)
        if BASE_URL not in full_url:
            continue
        slug = href.rstrip("/").split("/")[-1]
        if not slug or slug in seen:
            continue
        seen.add(slug)
        cats.append(CategoryItem(name=text, url=full_url, slug=slug))
    return {"results": cats}


@app.get("/category/{slug}")
@limiter.limit("10/minute")
async def category(request: Request, slug: str, page: int = Query(1, ge=1)):
    url = f"{BASE_URL}/category/{slug}/" if page == 1 else f"{BASE_URL}/category/{slug}/page/{page}/"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    results = parse_app_items(soup, "article, .post-item", limit=20, category=slug)
    if not results:
        raise HTTPException(404, f"No apps found for '{slug}'. Check /categories for valid slugs.")
    return {"page": page, "category": slug, "results": results}


@app.get("/search")
@limiter.limit("15/minute")
async def search(request: Request, q: str = Query(..., min_length=2), page: int = Query(1, ge=1)):
    url = f"{BASE_URL}/page/{page}/?s={quote_plus(q)}" if page > 1 else f"{BASE_URL}/?s={quote_plus(q)}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    results = parse_app_items(soup, "article, .post-item", limit=20)
    return {"query": q, "page": page, "results": results}


@app.get("/app")
@limiter.limit("10/minute")
async def app_detail(request: Request, url: str = Query(...)):
    if not url.startswith("https://apkdone.com/"):
        raise HTTPException(400, "Only https://apkdone.com/ URLs are allowed.")

    html = await fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    title = soup.select_one("h1")
    title = title.get_text(strip=True) if title else "Unknown App"
    slug = url.rstrip("/").split("/")[-1]

    # Logo
    logo = None
    for img in soup.select("img"):
        src = img.get("data-src") or img.get("src") or ""
        if src and any(k in src.lower() for k in ("logo", "icon", "app")):
            logo = urljoin(BASE_URL, src)
            break
    if not logo:
        fi = soup.select_one("article img, .post img, .entry img")
        logo = get_img(fi)

    text = soup.get_text()
    version  = re.search(r"Version[:\s]*v?([0-9][^\n\r\t]{0,30})", text, re.I)
    size     = re.search(r"Size[:\s]*([0-9][0-9.]*\s*[MGKmgk][Bb])", text)
    updated  = re.search(r"Updated?[:\s]*([A-Za-z0-9, ]+)", text)
    requires = re.search(r"Requires Android[:\s]*([^\n\r]{3,30})", text, re.I)

    desc_tag = soup.select_one(".entry-content, .description, .post-content, article, main")
    description = desc_tag.get_text(strip=True)[:1500] if desc_tag else ""

    links, seen_hrefs = [], set()
    for a in soup.select(
        "a[href*='download'], a.button, a.btn, .download-link, "
        "a[href$='.apk'], a[href$='.xapk'], a[href*='/dl/'], a[href*='/get/']"
    ):
        href = urljoin(BASE_URL, a.get("href", ""))
        if not href or href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        links.append(DownloadLink(name=a.get_text(strip=True) or "Download APK", original_url=href))
        if len(links) >= 10:
            break

    detail = AppDetail(
        title=title, slug=slug, url=url, logo=logo,
        version=version.group(1).strip() if version else "N/A",
        size=size.group(1).strip() if size else None,
        updated=updated.group(1).strip() if updated else None,
        requires_android=requires.group(1).strip() if requires else None,
        description=description,
        download_links=links,
    )

    # Attach hidden download URLs
    for i, link in enumerate(detail.download_links):
        cid = f"{slug}-{i+1}"
        download_cache[cid] = link.original_url
        link.clean_url = f"/d/{cid}"

    return detail


@app.get("/d/{download_id}")
@limiter.limit("8/minute")
async def hidden_download(request: Request, download_id: str):
    original = download_cache.get(download_id)
    if not original:
        raise HTTPException(404, "Link expired. Call /app again to refresh.")
    return RedirectResponse(url=original, status_code=302)
