import asyncio
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv
import os
import time

# Load credentials from .env
load_dotenv(override=True)
USERNAME = os.getenv("MOODLE_USERNAME")
PASSWORD = os.getenv("MOODLE_PASSWORD")

def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")

async def handle_login_flow(page: Page):
    print(USERNAME)
    print(PASSWORD)
    if "login" in page.url:
        print("🔐 Login page detected.")
        await page.wait_for_selector('input[name="username"]')
        await page.wait_for_selector('input[name="password"]')

        await page.fill('input[name="username"]', USERNAME or "")
        await page.fill('input[name="password"]', PASSWORD or "")

        try:
            await page.click('button[type="submit"]')
        except:
            await page.click('input#loginbtn')

        await page.wait_for_load_state("networkidle", timeout=60000)

        if "login" in page.url:
            print("❌ Login failed. Still on login page.")
        else:
            print("✅ Login successful. URL:", page.url)
    else:
        print("✅ Already logged in or no login required.")

async def expand_internal_toggles(page: Page):
    # Stub: insert code to click on any "expand" elements
    pass

async def extract_links(page: Page, url: str, session_id: int, module_id: int):
    anchors = await page.query_selector_all("a[href]")
    links = []
    for anchor in anchors:
        href = await anchor.get_attribute("href")
        if href and href.startswith("http"):
            links.append(href)
    return links

async def crawl_page(page: Page, url: str, session_id: int, module_id: int):
    print(f"🌐 Visiting: {url}")
    try:
        await page.goto(url, timeout=120000)  # long timeout for slow Moodle
        await page.wait_for_selector("body", timeout=60000)
    except Exception as e:
        print(f"⚠️ Failed to load: {url} — {e}")
        return []

    if "login" in page.url or "Continue" in await page.content():
        await handle_login_flow(page)

    await expand_internal_toggles(page)
    return await extract_links(page, url, session_id, module_id)

async def run_crawler(start_url: str, session_id: int, module_id: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        to_visit = [start_url]
        visited_normalized = set()
        visited_original = []

        while to_visit:
            current = to_visit.pop(0)
            norm = normalize_url(current)
            if norm in visited_normalized:
                continue
            visited_normalized.add(norm)

            print("🕷️ Crawling:", current)
            new_links = await crawl_page(page, current, session_id, module_id)
            visited_original.append(current)

            for link in new_links:
                norm_link = normalize_url(link)
                if norm_link not in visited_normalized:
                    to_visit.append(link)

            await asyncio.sleep(0.5)

        await browser.close()

        print("\n✅ Crawl complete.")
        print(f"🔄 Total unique pages visited: {len(visited_original)}")
        for url in visited_original:
            print(f" - {url}")
