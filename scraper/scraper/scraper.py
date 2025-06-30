import asyncio
import os
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page
import requests
from urllib.parse import urljoin, urlparse
import aiohttp
import filetype  # pip install filetype
from datetime import datetime, UTC

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


def detect_file_type(url, session):
    try:
        response = session.get(url, stream=True, timeout=10)
        chunk = next(response.iter_content(4096))  # Just the first chunk

        kind = filetype.guess(chunk)
        return kind.mime if kind else "unknown"
    except Exception as e:
        return f"Error: {e}"


def get_mime_type(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        content_type = response.headers.get("Content-Type", "unknown")
        print(response.status_code)
        print(response.url)
        print(response.text)
        return content_type
    except requests.RequestException as e:
        return f"Error: {e}"


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


def isExternal(url: str) -> bool:
    return not is_internal(url) or should_exclude_url(url)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    important_keys = {"id", "d", "cmid", "attempt"}
    filtered_query = {k: v for k, v in query.items() if k in important_keys}
    normalized_query = urlencode(filtered_query, doseq=True)
    return urlunparse(parsed._replace(query=normalized_query, fragment=""))


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
            await page.click("input#loginbtn")

        await page.wait_for_load_state("networkidle")

        if "login" in page.url:
            print("❌ Login failed. Still on login page.")
        else:
            print("✅ Login successful. URL:", page.url)
    else:
        print("✅ Already logged in or no login required.")


async def expand_internal_toggles(page: Page):
    toggles = await page.query_selector_all(
        '#page-content a[data-for="sectiontoggler"]'
    )

    if not toggles:
        print("No section toggles found.")
        return

    for toggle in toggles:
        try:
            await toggle.click()
        except Exception as e:
            print(f"⚠️ Failed to click toggle: {e}")


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


from urllib.parse import urlparse
from datetime import datetime
import os
import requests


def getFileExtension(ftype: str) -> str:
    # Common MIME to extension map
    mime_to_ext = {
        "pdf": ".pdf",
        "zip": ".zip",
        "msword": ".docx",
        "vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "vnd.ms-powerpoint": ".ppt",
        "vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "vnd.ms-excel": ".xls",
        "octet-stream": ".bin",  # generic fallback
        "x-executable": ".exe",
        "x-msdownload": ".exe",
        "x-sh": ".sh",
        "x-python": ".py",
        "json": ".json",
        "x-html": ".html",
        "x-zip-compressed": ".zip",
        "x-rar-compressed": ".rar",
    }

    try:
        subtype = ftype.split("/")[1]
        return mime_to_ext.get(subtype, f".{subtype}")
    except IndexError:
        return ".bin"


import os
from datetime import datetime


async def storeTempRepoWithPlaywright(page, url: str, ftype: str):
    if not ftype.startswith("text/html"):
        try:
            # Go to file URL directly
            response = await page.request.get(url)
            if response.status != 200:
                print(f"❌ Response error: {response.status} for {url}")
                return None

            fileExtension = getFileExtension(ftype)
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"tempFile{fileExtension}")

            content = await response.body()
            with open(temp_path, "wb") as f:
                f.write(content)

            print(f"📥 Stored (Playwright): {url} → {temp_path}")
            return temp_path

        except Exception as e:
            print(f"❌ Failed to download via Playwright: {url} — {e}")
            return None


from playwright.async_api import Page
from urllib.parse import urljoin


import re


import re
from playwright.async_api import Page


import re
from playwright.async_api import Page


import re
from playwright.async_api import Page


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

    linksToCrawlFurther = []
    external_links = []

    link_targets = []
    for a in anchors:
        try:
            if await a.get_attribute("data-region") == "post-action":
                continue
            href = await a.get_attribute("href")
            if href and not href.startswith("#"):
                classes = await a.get_attribute("class") or ""
                if "btn" in classes:
                    continue  # Ignore styled buttons
                full_url = urljoin(base_url, href)
                link_targets.append(full_url)
        except:
            continue  # Skip any broken anchors

    for full_url in link_targets:
        # If mod/resource: resolve final destination
        if "mod/resource/view.php" in full_url:
            try:
                real_file_url = await resolve_final_resource_url(page, full_url)
                print(f"📎 Found file: {real_file_url} — from {full_url}")
                if real_file_url:
                    file_type = await get_content_type_with_playwright(
                        page.context, real_file_url
                    )
                    print(f"📎 File Type: {file_type}")
                    if not is_internal(real_file_url):
                        external_links.append(real_file_url)
                    else:
                        if file_type.startswith("text/html"):
                            linksToCrawlFurther.append(real_file_url)
                        else:
                            print("file to be downloaded and scanned further")
                continue  # Skip duplicate internal check
            except Exception as e:
                print(f"❌ Failed to resolve file: {e}")

        # General internal/external handling
        file_type = await get_content_type_with_playwright(page.context, full_url)

        if should_exclude_url(full_url):
            print(f"🚫 Skipping excluded internal URL: {full_url}")
            continue

        if is_internal(full_url):
            print(f"INTERNAL URL: {file_type} — {full_url}")
            if file_type.startswith("text/html"):
                linksToCrawlFurther.append(full_url)
        else:
            print("EXTERNAL URL DETECTED")
            external_links.append(full_url)
            post_scraped_link(session_id, module_id, full_url)

    print(f"[INTERNAL LINKS] Found {len(linksToCrawlFurther)} at: {base_url}")
    print(f"[EXTERNAL LINKS] Found {len(external_links)} at: {base_url}")
    return linksToCrawlFurther


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
            print("at run crawler")
            print("going to crawl_age")

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
