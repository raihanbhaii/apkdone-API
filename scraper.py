import asyncio
import random
import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from models import AppDetail, AppItem, DownloadLink, OldVersion

BASE_URL = "https://apkdone.com"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
]

async def stealth_browser(proxy: Optional[str] = None):
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        proxy={"server": proxy} if proxy else None,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    context = await browser.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent=random.choice(USER_AGENTS)
    )
    # Basic stealth
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """)
    page = await context.new_page()
    return p, browser, page

async def get_final_direct_apk_url(page_url: str, proxy: Optional[str] = None) -> Optional[str]:
    p, browser, page = await stealth_browser(proxy)
    try:
        await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)

        # Click download buttons if present
        for sel in ["a:has-text('Download')", ".download-button", "a.button", "a[href*='download']"]:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(5000)
                    break
            except:
                continue

        # Extract direct APK links
        links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href)
                .filter(h => /\\.apk$|\\.xapk$|download.*apk/i.test(h))
        """)
        
        if links:
            return max(links, key=lambda x: (x.endswith(('.apk', '.xapk')), len(x)))
        return None
    finally:
        await browser.close()
        await p.stop()

# ... (search_apps and get_app_detail functions remain similar to previous version - I kept them short for space)

async def get_app_detail(app_url: str, proxy: Optional[str] = None) -> AppDetail:
    # Full implementation (same as before) - extracts logo, screenshots, old versions, etc.
    # For brevity here: assume you copy the detailed version from my earlier response
    # Key point: it populates download_links with original_url
    pass  # Replace with full scraper code from previous messages if needed
