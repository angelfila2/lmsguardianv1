import os
import re
import asyncio
import requests
from datetime import datetime
from urllib.parse import urljoin
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page
from scraper.utils import *
import hashlib
import pytz
from scraper.downloadfiles import *

load_dotenv(override=True)
USERNAME = os.getenv("MOODLE_USERNAME")
PASSWORD = os.getenv("MOODLE_PASSWORD")

# FOR LOCAL
# BASE_URL = "http://3.107.195.248/moodle/course/view.php?id="
# MOODLE_DOMAIN = "3.107.195.248"

# FOR PRODUCTION ENVIORNMENT
BASE_URL = "http://10.51.33.25/moodle/course/view.php?id="
MOODLE_DOMAIN = "10.51.33.25"

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
    "/moodle/user",
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
    sg = pytz.timezone("Asia/Singapore")
    formattedSGtime = datetime.now(sg)
    print(formattedSGtime)
    payload = {
        "module_id": module_id,
        "session_id": session_id,
        "url_link": url_link,
        "scraped_at": formattedSGtime.isoformat(),
        "risk_status": risk_status,
        "is_paywall": is_paywall,
        "content_location": content_location,
        "apa7": apa7,
    }
    try:
        response = requests.post("http://127.0.0.1:8000/scrapedcontents", json=payload)
        response.raise_for_status()
        print(f"✅ Link stored: {url_link}")
    except Exception as e:
        print(f"❌ Failed to store link: {url_link} — {e}")


async def handle_login_flow(page: Page):
    print("Starting login flow...")
    print("USERNAME:", USERNAME)
    print("PASSWORD:", PASSWORD)

    if "login" in page.url:
        print("?? Login page detected.")

        # ? Ensure full page load before interacting
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector('input[name="username"]')
        await page.wait_for_selector('input[name="password"]')

        # ?? Screenshot before filling
        await page.screenshot(path="step1_login_page.png")

        # Fill credentials
        await page.fill('input[name="username"]', USERNAME or "")
        await page.fill('input[name="password"]', PASSWORD or "")

        # ?? Screenshot after filling credentials
        await page.screenshot(path="step2_filled_credentials.png")

        # Try clicking the login button (supports both button types)
        try:
            await page.click('button[type="submit"]')
        except Exception:
            try:
                await page.click("input#loginbtn")
            except Exception as e:
                print(f"? Could not click login button: {e}")
                await page.screenshot(path="step2b_click_error.png")
                return

        # Wait for next page to load
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="step3_after_submit.png")

        # Check if login was successful
        if "login" in page.url:
            print("? Login failed. Still on login page.")
            html = await page.content()
            with open("login_failed_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
        else:
            print(f"? Login successful. URL: {page.url}")
            await page.screenshot(path="step4_login_success.png")
    else:
        print("? Already logged in or no login required.")


async def expand_internal_toggles(page: Page):
    toggles = await page.query_selector_all(
        '#page-content a[data-for="sectiontoggler"]'
    )

    if not toggles:
        print("No section toggles found.")
        return

    for toggle in toggles:
        try:
            is_expanded = await toggle.get_attribute("aria-expanded")
            if is_expanded == "false":
                await toggle.click()
                print("✅ Toggle clicked to expand section.")
            else:
                print("⏭️ Section already expanded. Skipping.")
        except Exception as e:
            print(f"⚠️ Failed to handle toggle: {e}")


async def get_content_type_with_playwright(context, url: str) -> str:
    content_type_result = "unknown"
    page = await context.new_page()

    def handle_response(response):
        nonlocal content_type_result
        if response.url == url:
            headers = response.headers
            content_type_result = headers.get("content-type", "unknown")

    page.on("response", handle_response)

    try:
        await page.goto(url, wait_until="load", timeout=60000)
    except Exception as e:
        if "net::ERR_ABORTED" not in str(e) and "pluginfile.php" not in url:
            print(f"⚠️ Failed to load {url} — {e}")
    finally:
        await page.close()

    return content_type_result


async def storeTempRepoWithPlaywright(page: Page, url: str, ftype: str) -> str | None:
    if is_possibly_malicious(url, ftype):
        print(f"⚠️ Skipped potentially dangerous file: {url} ({ftype})")
        return None

    if not ftype.startswith("text/html"):
        try:
            response = await page.request.get(url)
            if response.status != 200:
                print(f"❌ Response error: {response.status} for {url}")
                return None

            file_extension = getFileExtension(ftype)
            target_dir = os.path.join("scraper", "scraper", "toProcessFurther")
            os.makedirs(target_dir, exist_ok=True)

            # 🔐 Use SHA256 hash of URL for unique filename
            hashed = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
            filename = f"{hashed}{file_extension}"
            save_path = os.path.join(target_dir, filename)

            content = await response.body()
            with open(save_path, "wb") as f:
                f.write(content)

            print(f"📥 SAVED: {url} → {save_path}")
            return save_path

        except Exception as e:
            print(f"❌ Failed to download via Playwright: {url} — {e}")
            return None


async def resolve_final_resource_url(page: Page, url: str) -> str | None:
    """
    Resolves the actual file or external content URL behind a Moodle mod/resource link.
    Handles direct pluginfile URLs, downloads, iframe previews, and HTML-based redirects.
    """

    file_extensions = [
        ".pdf",
        ".docx",
        ".pptx",
        ".zip",
        ".doc",
        ".ppt",
        ".xls",
        ".xlsx",
    ]

    def looks_like_file_url(u: str) -> bool:
        last_segment = re.split(r"[/?&]", u.split("/")[-1])[-1].lower()
        return any(last_segment.endswith(ext) for ext in file_extensions)

    # 🥇 0. Direct file URL (Method 2 first)
    if looks_like_file_url(url):
        print("METHOD 2 (FAST) \n")
        print(f"📄 URL already looks like a file: {url}")
        return url

    # 🧼 1. Sanity check for typical Moodle mod/resource links
    if not re.search(r"/mod/resource/view\.php\?id=\d+", url):
        print(f"⚠️ Malformed or suspicious resource URL skipped: {url}")
        return None

    # 🥈 2. Try to detect file request for known extensions
    try:
        async with page.expect_request(
            lambda r: any(ext in r.url.lower() for ext in file_extensions),
            timeout=8000,
        ) as req_info:
            try:
                await page.goto(url, wait_until="commit")
            except Exception as e:
                print(f"⚠️ Navigation error (request-level): {e}")
        request = await req_info.value
        print("METHOD 2 \n")
        print(f"🔗 File request captured: {request.url}")
        return request.url
    except Exception as e:
        print(f"🕵️ No direct file request captured: {e}")

    # 🥉 3. Fallback: Try to capture a file download (Method 1)
    try:
        async with page.expect_download(timeout=10000) as download_info:
            try:
                await page.goto(url, wait_until="commit")
            except Exception as e:
                print(f"⚠️ Navigation interrupted (likely due to download): {e}")
        download = await download_info.value
        print("METHOD 1 \n")
        print(f"📥 Detected file download: {download.url}")
        return download.url
    except Exception as e:
        print(f"🕵️ No file download captured: {e}")

    # 🏁 4. Fallback: Check for iframe or redirect-based HTML structures
    try:
        await page.goto(url, wait_until="domcontentloaded")

        for frame in page.frames:
            if frame.url != page.url:
                print("METHOD 3 \n")
                print(f"🖼️ Iframe found: {frame.url}")
                return frame.url

        html = await page.content()

        match_meta = re.search(
            r'<meta http-equiv=["\']refresh["\'] content=["\']\d+;url=([^"\']+)',
            html,
            re.IGNORECASE,
        )
        if match_meta:
            redirect_url = match_meta.group(1)
            print("METHOD 3 \n")
            print(f"🔁 Meta refresh detected: {redirect_url}")
            return redirect_url

        match_js = re.search(r'window\.location\s*=\s*["\']([^"\']+)', html)
        if match_js:
            redirect_url = match_js.group(1)
            print("METHOD 3 \n")
            print(f"🔁 JS redirect detected: {redirect_url}")
            return redirect_url

    except Exception as e:
        print(f"❌ Fallback parsing failed: {e}")

    print("🚫 No file, iframe, or redirect target found.")
    return None


async def extract_links(page: Page, base_url: str, session_id: int, module_id: int):
    await page.wait_for_selector("#page-content")
    anchors = await page.query_selector_all("#page-content a")

    links_to_crawl_further = []
    external_links = []
    collected_links = []

    for anchor in anchors:
        try:
            if await anchor.get_attribute("data-region") == "post-action":
                continue
            href = await anchor.get_attribute("href")
            if href and not href.startswith("#"):
                class_attr = await anchor.get_attribute("class") or ""
                if "btn" in class_attr:
                    continue  # Skip navigation buttons
                full_url = urljoin(base_url, href)
                collected_links.append(full_url)
        except:
            continue

    for full_url in collected_links:
        if "mod/resource/view.php" in full_url:
            try:
                resolved_url = await resolve_final_resource_url(page, full_url)
                print(f"📎 Found file: {resolved_url} — from {full_url}")
                if not resolved_url:
                    continue

                if should_exclude_url(resolved_url):
                    print(f"🚫 Skipping excluded internal URL: {resolved_url}")
                    continue

                if not is_internal(resolved_url):
                    print("EXTERNAL FILE URL DETECTED")
                    external_links.append(resolved_url)
                    post_scraped_link(session_id, module_id, resolved_url)
                    continue

                mime_type = await get_content_type_with_playwright(
                    page.context, resolved_url
                )
                print(f"📎 File Type: {mime_type}")

                if mime_type.startswith("text/html"):
                    links_to_crawl_further.append(resolved_url)
                else:
                    if not is_possibly_malicious(resolved_url, mime_type):
                        await storeTempRepoWithPlaywright(page, resolved_url, mime_type)
                        print("📥 Internal file saved for processing")

                continue
            except Exception as e:
                print(f"❌ Failed to resolve file: {e}")
                continue

        if should_exclude_url(full_url):
            print(f"🚫 Skipping excluded internal URL: {full_url}")
            continue

        if not is_internal(full_url):
            print("EXTERNAL URL DETECTED")
            external_links.append(full_url)
            post_scraped_link(session_id, module_id, full_url)
            continue

        mime_type = await get_content_type_with_playwright(page.context, full_url)

        if not is_possibly_malicious(full_url, mime_type):
            await storeTempRepoWithPlaywright(page, full_url, mime_type)

        print(f"INTERNAL URL: {mime_type} — {full_url}")

        if mime_type.startswith("text/html"):
            links_to_crawl_further.append(full_url)
        else:
            print("📥 Internal file saved for processing")

    print(f"[INTERNAL LINKS] Found {len(links_to_crawl_further)} at: {base_url}")
    print(f"[EXTERNAL LINKS] Found {len(external_links)} at: {base_url}")
    return links_to_crawl_further


async def crawl_page(page: Page, url: str, session_id: int, module_id: int):
    print(f"🌐 Visiting: {url}")
    try:
        # await page.goto(url, timeout=10000)
        await page.goto(url, wait_until="load")

    except:
        print(f"⚠️ Failed to load: {url}")
        return []

    if "login" in page.url or "Continue" in await page.content():
        await handle_login_flow(page)
    await page.goto(url, wait_until="load")
    meta_tags = await page.query_selector_all("meta[content]")
    for tag in meta_tags:
        content_val = await tag.get_attribute("content")
        print(f"✅ Meta content value: {content_val}")
    title = await page.title()
    print(f"📄 Page title: {title}")
    course_id = await page.evaluate("() => window.M && M.cfg && M.cfg.courseId")
    print(f"🎯 Course ID (from M.cfg): {course_id}")

    await expand_internal_toggles(page)
    return await extract_links(page, url, session_id, module_id)


async def run_crawler(starting_page: str, session_id: int, module_id: int):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        pages_to_check = [starting_page]
        pages_already_seen = set()
        pages_visited = []

        while pages_to_check:
            current_page = pages_to_check.pop(0)
            clean_page_url = normalize_url(current_page)

            if clean_page_url in pages_already_seen:
                continue

            pages_already_seen.add(clean_page_url)
            print(f"🔍 Checking: {current_page}")

            found_links = await crawl_page(page, current_page, session_id, module_id)

            pages_visited.append(current_page)

            for link in found_links:
                clean_link = normalize_url(link)
                print(f"🔗 Cleaned link: {clean_link}")

                if clean_link not in pages_already_seen:
                    pages_to_check.append(clean_link)

            await asyncio.sleep(0.5)
        # second loop
        downloaded_links = downloadFilesAndCheck()
        unique_links = list(set(downloaded_links))

        for link in unique_links:
            post_scraped_link(session_id,module_id,link)
        await browser.close()

        print("\n✅ All done crawling.")
        print(f"📌 Pages visited: {len(pages_visited)}")
        for url in pages_visited:
            print(f" - {url}")
