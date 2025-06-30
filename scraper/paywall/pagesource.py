from playwright.sync_api import sync_playwright

def apply_manual_stealth(page):
    page.add_init_script("""Object.defineProperty(navigator, 'webdriver', {get: () => false})""")
    page.add_init_script("""window.chrome = { runtime: {} }""")
    page.add_init_script("""Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})""")
    page.add_init_script("""Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})""")

def load_and_save_page_source(url, filename):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True later if needed
        context = browser.new_context()
        page = context.new_page()

        apply_manual_stealth(page)

        print(f"🌐 Loading: {url}")
        page.goto(url, timeout=20000)
        page.wait_for_timeout(6000)  # Let JavaScript finish loading

        # Save page source
        html = page.content()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Saved page source to {filename}")
        browser.close()

# === Main Execution ===
urls = [
    "https://www.wsj.com/finance/banking/goldman-sachs-greece-hotel-sell-34b5353a",
    "https://www.bloomberg.com/news/articles/2025-06-28/tsmc-affiliate-vis-may-expedite-production-at-8-billion-singapore-fab",
]

for i, url in enumerate(urls):
    filename = f"page_source_{i+1}.html"
    load_and_save_page_source(url, filename)
