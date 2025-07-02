import asyncio
from playwright.async_api import async_playwright
import os

import asyncio
from playwright.async_api import async_playwright
import os
import os
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


async def save_webpage_complete(module_name, url):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "localrepo", module_name)
    asset_dir = os.path.join(base_dir, "assets")
    os.makedirs(asset_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    session = aiohttp.ClientSession()

    # Collect asset URLs
    asset_tags = {
        "img": "src",
        "link": "href",
        "script": "src",
    }

    for tag, attr in asset_tags.items():
        for element in soup.find_all(tag):
            link = element.get(attr)
            if not link or link.startswith("data:"):
                continue

            full_url = urljoin(url, link)
            parsed = urlparse(full_url)
            filename = os.path.basename(parsed.path)
            local_path = os.path.join("assets", filename)

            # Download and rewrite
            try:
                async with session.get(full_url) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        with open(os.path.join(asset_dir, filename), "wb") as f:
                            f.write(content)
                        element[attr] = local_path
            except Exception as e:
                print(f"❌ Failed to get {full_url}: {e}")

    await session.close()

    # Save final HTML
    filename = urlparse(url).path.split("/")[-1] or "index"
    filename = "".join(c if c.isalnum() else "-" for c in filename.lower()) + ".html"
    final_html_path = os.path.join(base_dir, filename)
    with open(final_html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"✅ Saved full page: {final_html_path}")


if __name__ == "__main__":
    asyncio.run(
        save_webpage_complete(
            module_name="module1",
            url="https://saturncloud.io/blog/how-to-read-data-from-google-sheets-using-colaboratory-google/",
        )
    )
