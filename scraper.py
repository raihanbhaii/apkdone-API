import asyncio
import re
import hashlib
from urllib.parse import urljoin
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from models import AppDetail, AppItem, DownloadLink

BASE_URL = "https://apkdone.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text

async def get_final_direct_apk_url(page_url: str) -> Optional[str]:
    """Light version: just return the download page URL itself (user will be redirected to it)"""
    # On free tier we can't reliably extract final .apk link without browser
    # So we redirect to the original download page on apkdone.com
    return page_url

async def get_app_detail(app_url: str) -> AppDetail:
    html = await fetch_html(app_url)
    soup = BeautifulSoup(html, "lxml")

    title = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "Unknown"
    slug = app_url.rstrip("/").split("/")[-1]

    logo = None
    img = soup.select_one("img")
    if img and img.get("src"):
        logo = urljoin(BASE_URL, img["src"])

    text = soup.get_text()
    version = re.search(r"Version[:\s]*([^\n]+)", text)
    size_match = re.search(r"Size[:\s]*([0-9.]+\s*[MGK]B)", text)
    updated = re.search(r"Updated?[:\s]*([^\n]+)", text)
    requires = re.search(r"Requires Android[:\s]*([^\n]+)", text)

    description = ""
    desc_tag = soup.select_one(".entry-content, .description, .post-content")
    if desc_tag:
        description = desc_tag.get_text(strip=True)[:1200]

    # Download links
    download_links = []
    for a in soup.select("a[href*='download'], a.button, a[href*='.apk'], a[href*='.xapk']"):
        href = urljoin(BASE_URL, a.get("href", ""))
        if href and ("download" in href.lower() or href.lower().endswith(('.apk', '.xapk'))):
            download_links.append(DownloadLink(
                name=a.get_text(strip=True) or "Download APK",
                original_url=href
            ))

    return AppDetail(
        title=title,
        slug=slug,
        url=app_url,
        logo=logo,
        version=version.group(1).strip() if version else "N/A",
        size=size_match.group(1) if size_match else None,
        updated=updated.group(1).strip() if updated else None,
        requires_android=requires.group(1).strip() if requires else None,
        description=description,
        download_links=download_links[:8],
    )

async def search_apps(query: str, page: int = 1) -> List[AppItem]:
    url = f"{BASE_URL}/?s={query}"
    if page > 1:
        url += f"&page={page}"
    
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    
    apps = []
    for item in soup.select("article, .post-item, li"):
        a = item.select_one("h2 a, h3 a, .title a")
        img = item.select_one("img")
        if a:
            apps.append(AppItem(
                title=a.get_text(strip=True),
                url=urljoin(BASE_URL, a["href"]),
                image=urljoin(BASE_URL, img["src"]) if img and img.get("src") else None
            ))
    return apps
