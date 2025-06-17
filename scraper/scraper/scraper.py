import asyncio
import os
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page
import requests
from datetime import datetime

# --- Load credentials ---
load_dotenv()
USERNAME = os.getenv("MOODLE_USERNAME")
PASSWORD = os.getenv("MOODLE_PASSWORD")
BASE_URL = "http://3.107.195.248/moodle/course/view.php?id="
MOODLE_DOMAIN = "3.107.195.248"

EXCLUDED_PATH_PREFIXES = [
    "/moodle/user/",
    "/moodle/message/",
    "/moodle/notes/",
    "/moodle/blog/",
    "/moodle/iplookup/",
    "/moodle/tag/",
    "/moodle/calendar/",
    "/moodle/report/usersessions/",
    "/moodle/admin/",
    "/moodle/enrol/",
    "/moodle/grade/report/overview/",
    "/moodle/competency/",
]


def post_scraped_link(
    session_id: int,
    module_id: int,
    url_link: str,
    risk_status: str = "unknown",
    is_paywall: bool = False,
    content_location: str = None,
    apa7: str = None,
):
    payload = {
        "module_id": module_id,
        "session_id": session_id,
        "url_link": url_link,
        "scraped_at": datetime.utcnow().isoformat(),
        "risk_status": risk_status,
        "is_paywall": is_paywall,
        "content_location": content_location,
        "apa7": apa7,
    }
    try:
        response = requests.post("http://127.0.0.1:8000/scraped-contents", json=payload)
        response.raise_for_status()
        print(f"✅ Link stored: {url_link}")
    except Exception as e:
        print(f"❌ Failed to store link: {url_link} — {e}")


def should_exclude_url(url: str) -> bool:
    path = urlparse(url).path
    return any(path.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)


def is_internal(url: str) -> bool:
    return urlparse(url).netloc == MOODLE_DOMAIN


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    important_keys = {"id", "d", "cmid", "attempt"}
    filtered_query = {k: v for k, v in query.items() if k in important_keys}
    normalized_query = urlencode(filtered_query, doseq=True)
    return urlunparse(parsed._replace(query=normalized_query, fragment=""))


async def handle_login_flow(page: Page):
    try:
        await page.wait_for_selector("text=Continue", timeout=3000)
        print("👉 Clicking 'Continue'...")
        await page.click("text=Continue")
    except:
        pass

    if "login" in page.url:
        print("🔐 Logging in...")
        await page.fill('input[name="username"]', USERNAME or "")
        await page.fill('input[name="password"]', PASSWORD or "")
        await page.click('button[type="submit"]')


async def expand_internal_toggles(page: Page):
    toggles = await page.query_selector_all(
        '#page-content a[data-for="sectiontoggler"]'
    )
    for t in toggles:
        try:
            await t.click()
        except:
            continue


async def extract_links(page: Page, base_url: str, session_id: int, module_id: int):
    await page.wait_for_selector("#page-content", timeout=5000)
    anchors = await page.query_selector_all("#page-content a")
    internal_links = []
    external_links = []

    for a in anchors:
        if await a.get_attribute("data-region") == "post-action":
            continue
        href = await a.get_attribute("href")
        if href and not href.startswith("#"):
            full_url = urljoin(base_url, href)
            if is_internal(full_url) and not should_exclude_url(full_url):
                internal_links.append(full_url)
            elif not is_internal(full_url):
                external_links.append(full_url)
                try:
                    r = requests.get(full_url, timeout=10)
                    r.raise_for_status()

                    # --- STEP 2: Generate local path ---]
                    
                    parsed = urlparse(full_url)
                    parsed_path = parsed.path.rstrip("/") 
                    filename = os.path.basename(parsed_path)
                    if not filename:  # fallback if URL ends with /
                        filename = f"resource_{datetime.utcnow().timestamp():.0f}.html"

                    local_dir = f"localrepo/module_{module_id}"
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = os.path.join(local_dir, filename)

                    # --- STEP 3: Save the content ---
                    with open(local_path, "wb") as f:
                        f.write(r.content)

                    print(f"📥 Downloaded: {full_url} → {local_path}")

                except Exception as e:
                    print(f"❌ Failed to download: {full_url} — {e}")
                    local_path = None
                post_scraped_link(session_id, module_id, full_url)

    print(f"🔗 Found {len(internal_links)} internal links at: {base_url}")
    print(f"🌍 Found {len(external_links)} external links at: {base_url}")
    return internal_links


async def crawl_page(page: Page, url: str, session_id: int, module_id: int):
    print(f"🌐 Visiting: {url}")
    try:
        await page.goto(url, timeout=10000)
    except:
        print(f"⚠️ Failed to load: {url}")
        return []

    if "login" in page.url or "Continue" in await page.content():
        await handle_login_flow(page)

    await expand_internal_toggles(page)
    return await extract_links(page, url, session_id, module_id)


async def run_crawler(start_url: str, session_id: int, module_id: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
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


def get_module_ids():
    try:
        response = requests.get("http://127.0.0.1:8000/moduleid")
        response.raise_for_status()
        return response.json()  # this will be a list of ints like [1, 2, 3]
    except Exception as e:
        print(f"❌ Failed to fetch module IDs: {e}")
        return []


def getLatestRiskSessions():
    response = requests.get("http://127.0.0.1:8000/risks")
    return response.json()


# === MAIN TEST ===
if __name__ == "__main__":

    base_url = "http://3.107.195.248/moodle/course/view.php?id=2"
