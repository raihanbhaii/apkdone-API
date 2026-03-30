import re
import hashlib
from urllib.parse import urljoin, quote_plus
from typing import List, Optional, Any

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

# ── Models ────────────────────────────────────────────────────────────────────

class DownloadLink(BaseModel):
    name: str
    original_url: str
    clean_url: Optional[str] = None

class AppDetail(BaseModel):
    title: str
    slug: str
    url: str
    logo: Optional[str] = None
    version: str = "N/A"
    size: Optional[str] = None
    updated: Optional[str] = None
    requires_android: Optional[str] = None
    description: str = ""
    download_links: List[DownloadLink] = []

class AppItem(BaseModel):
    title: str
    url: str
    image: Optional[str] = None

# ── Config ────────────────────────────────────────────────────────────────────

BASE = "https://apkdone.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

download_cache: dict = {}

import os
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")

# ── FastAPI setup ─────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="APKDone API", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Core helpers ──────────────────────────────────────────────────────────────

async def fetch(url: str) -> BeautifulSoup:
    if not SCRAPER_API_KEY:
        raise RuntimeError("SCRAPER_API_KEY env variable is not set")
    api_url = "http://api.scraperapi.com"
    params = {"api_key": SCRAPER_API_KEY, "url": url}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as c:
        r = await c.get(api_url, params=params)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")

def img_src(tag) -> Optional[str]:
    if not tag:
        return None
    for attr in ("data-src", "data-lazy-src", "data-original", "src"):
        v = tag.get(attr, "")
        if v and not v.startswith("data:"):
            return urljoin(BASE, v)
    return None

CARD_SELECTORS = ["article", ".post-item", ".app-item", ".app-card", ".item", ".apk-item", "li.post", ".post", ".entry"]
LINK_SELECTORS = ["h1 a","h2 a","h3 a","h4 a",".title a",".app-name a",".entry-title a","a[rel='bookmark']"]

def parse_cards(soup: BeautifulSoup, limit: int = 24) -> List[AppItem]:
    results, seen = [], set()

    for sel in CARD_SELECTORS:
        cards = soup.select(sel)
        if len(cards) >= 3:
            for card in cards[:limit]:
                link = None
                for ls in LINK_SELECTORS:
                    link = card.select_one(ls)
                    if link:
                        break
                if not link:
                    link = card.select_one("a[href]")
                if not link:
                    continue
                href = urljoin(BASE, link.get("href", ""))
                if not href.startswith(BASE) or href in seen or href == BASE + "/":
                    continue
                seen.add(href)
                title = link.get_text(strip=True) or card.get_text(strip=True)[:60]
                image = img_src(card.select_one("img"))
                results.append(AppItem(title=title, url=href, image=image))
            if results:
                return results

    # Fallback: any internal link with a nearby image
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        if not href.startswith(BASE + "/") or href in seen:
            continue
        if any(x in href for x in ["#", "category", "tag", "/page/", "contact", "about", "wp-"]):
            continue
        img = a.find("img") or (a.parent and a.parent.find("img"))
        if not img:
            continue
        seen.add(href)
        results.append(AppItem(title=a.get_text(strip=True) or "Unknown", url=href, image=img_src(img)))
        if len(results) >= limit:
            break

    return results

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "OK",
        "endpoints": {
            "/home": "Homepage apps",
            "/trending": "Trending/popular apps",
            "/games": "Games category",
            "/categories": "All categories",
            "/category/{slug}": "Apps by category slug",
            "/search?q=": "Search",
            "/app?url=": "App detail + downloads",
        },
    }

@app.get("/home")
@limiter.limit("10/minute")
async def home(request: Request):
    try:
        soup = await fetch(BASE)
        apps = parse_cards(soup, 30)
        return {"featured": apps[:8], "new_apps": apps[8:18], "popular": apps[18:]}
    except Exception as e:
        raise HTTPException(502, detail=f"Homepage fetch failed: {e}")

@app.get("/trending")
@limiter.limit("10/minute")
async def trending(request: Request):
    for path in ["/trending/", "/popular/", "/most-downloaded/", "/"]:
        try:
            soup = await fetch(BASE + path)
            apps = parse_cards(soup, 20)
            if apps:
                return {"results": apps}
        except Exception:
            continue
    raise HTTPException(502, "Could not fetch trending")

@app.get("/games")
@limiter.limit("10/minute")
async def games(request: Request, page: int = Query(1, ge=1)):
    path = "/category/games/" if page == 1 else f"/category/games/page/{page}/"
    try:
        soup = await fetch(BASE + path)
        apps = parse_cards(soup, 20)
        return {"page": page, "results": apps}
    except Exception as e:
        raise HTTPException(502, detail=f"Games fetch failed: {e}")

@app.get("/categories")
@limiter.limit("10/minute")
async def categories(request: Request):
    try:
        soup = await fetch(BASE)
        cats, seen = [], set()
        for a in soup.select("a[href*='/category/']"):
            href = urljoin(BASE, a["href"])
            slug = href.rstrip("/").split("/")[-1]
            text = a.get_text(strip=True)
            if slug and slug not in seen and text:
                seen.add(slug)
                cats.append({"name": text, "url": href, "slug": slug})
        return {"results": cats}
    except Exception as e:
        raise HTTPException(502, detail=f"Categories fetch failed: {e}")

@app.get("/category/{slug}")
@limiter.limit("10/minute")
async def category(request: Request, slug: str, page: int = Query(1, ge=1)):
    path = f"/category/{slug}/" if page == 1 else f"/category/{slug}/page/{page}/"
    try:
        soup = await fetch(BASE + path)
        apps = parse_cards(soup, 20)
        if not apps:
            raise HTTPException(404, f"No apps found for category '{slug}'")
        return {"page": page, "category": slug, "results": apps}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, detail=f"Category fetch failed: {e}")

@app.get("/search")
@limiter.limit("15/minute")
async def search(request: Request, q: str = Query(..., min_length=2), page: int = Query(1, ge=1)):
    try:
        url = f"{BASE}/page/{page}/?s={quote_plus(q)}" if page > 1 else f"{BASE}/?s={quote_plus(q)}"
        soup = await fetch(url)
        apps = parse_cards(soup, 20)
        return {"query": q, "page": page, "results": apps}
    except Exception as e:
        raise HTTPException(502, detail=f"Search failed: {e}")

@app.get("/app")
@limiter.limit("10/minute")
async def app_detail(request: Request, url: str = Query(...)):
    if not url.startswith("https://apkdone.com/"):
        raise HTTPException(400, "Only https://apkdone.com/ URLs allowed")
    try:
        soup = await fetch(url)
    except Exception as e:
        raise HTTPException(502, detail=f"App page fetch failed: {e}")

    slug = url.rstrip("/").split("/")[-1]

    title = ""
    for sel in ["h1", ".entry-title", ".app-title", ".post-title", "h2"]:
        t = soup.select_one(sel)
        if t:
            title = t.get_text(strip=True)
            break
    title = title or slug

    logo = None
    for img in soup.select("img"):
        src = img_src(img)
        if src and any(k in (src or "").lower() for k in ("logo", "icon", "app", slug[:5])):
            logo = src
            break
    if not logo:
        first = soup.select_one(".entry-content img, article img, .post img")
        logo = img_src(first)

    text = soup.get_text(" ", strip=True)
    def rx(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else None

    version  = rx(r"Version[:\s]*v?([0-9][^\s]{0,20})")
    size     = rx(r"Size[:\s]*([0-9][0-9.]*\s*[MGKmgk][Bb])")
    updated  = rx(r"Updated?[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})")
    requires = rx(r"Requires Android[:\s]*([0-9.]+\+?)")

    desc = ""
    for sel in [".entry-content", ".description", ".post-content", "article"]:
        d = soup.select_one(sel)
        if d:
            desc = d.get_text(" ", strip=True)[:1500]
            break

    links, seen_h = [], set()
    for a in soup.select(
        "a[href*='download'], a[href$='.apk'], a[href$='.xapk'], "
        "a[href*='/dl/'], a[href*='/get/'], a.btn, a.button, .download-btn a"
    ):
        href = urljoin(BASE, a.get("href", ""))
        if not href or href in seen_h:
            continue
        seen_h.add(href)
        links.append(DownloadLink(name=a.get_text(strip=True) or "Download APK", original_url=href))
        if len(links) >= 8:
            break

    detail = AppDetail(
        title=title, slug=slug, url=url, logo=logo,
        version=version or "N/A",
        size=size, updated=updated, requires_android=requires,
        description=desc, download_links=links,
    )

    for i, lnk in enumerate(detail.download_links):
        cid = f"{slug}-{i+1}"
        download_cache[cid] = lnk.original_url
        lnk.clean_url = f"/d/{cid}"

    return detail

@app.get("/d/{did}")
@limiter.limit("8/minute")
async def download(request: Request, did: str):
    url = download_cache.get(did)
    if not url:
        raise HTTPException(404, "Link expired — call /app again to refresh")
    return RedirectResponse(url=url, status_code=302)
