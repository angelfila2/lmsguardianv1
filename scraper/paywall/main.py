from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def classify_page_access(url: str) -> dict:
    result = {"url": url, "status": None, "reason": None}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0")
            page.goto(url, wait_until="networkidle", timeout=20000)
            html = page.content()
            browser.close()
        except Exception as e:
            result["status"] = "unavailable"
            result["reason"] = f"Page load failed: {str(e)}"
            return result

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().strip().lower()

    # === Controlled Access Checks ===
    if "datadome" in html or "captcha" in text:
        result["status"] = "controlled_access"
        result["reason"] = "DataDome CAPTCHA or bot protection detected"
        return result

    if "cloudflare" in html and "cf-chl" in html:
        result["status"] = "controlled_access"
        result["reason"] = "Cloudflare bot challenge detected"
        return result

    if "please sign in" in text or "log in to continue" in text:
        result["status"] = "controlled_access"
        result["reason"] = "Login wall detected"
        return result

    # === Paywall Checks ===
    paywall_keywords = [
        "subscribe to continue",
        "already a subscriber",
        "you’ve reached your limit",
        "for subscribers only",
        "your trial has ended",
        "this content is for subscribers",
        "paywall",
    ]
    for keyword in paywall_keywords:
        if keyword in text:
            result["status"] = "paywalled"
            result["reason"] = f"Keyword match: '{keyword}'"
            return result

    # Look for common blocked or empty content containers
    blocked_selectors = [
        '[class*="paywall"]',
        '[id*="paywall"]',
        '[class*="overlay"]',
        '[class*="metered"]',
        '[class*="subscription"]',
        '[data-qa-id="paywall"]',
    ]
    for selector in blocked_selectors:
        if soup.select_one(selector):
            result["status"] = "paywalled"
            result["reason"] = f"Detected paywall-related element: {selector}"
            return result

    # Check for extremely short or generic content (possible blocking)
    body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
    if len(body_text) < 300:
        result["status"] = "paywalled"
        result["reason"] = (
            "Unusually short body text — possible paywall content removed"
        )
        return result

    # === Clean
    result["status"] = "clean"
    result["reason"] = "No access restrictions detected"
    return result


urls = [
    "https://www.wsj.com/finance/banking/goldman-sachs-greece-hotel-sell-34b5353a",
    "https://www.bloomberg.com/news/articles/2025-06-28/tsmc-affiliate-vis-may-expedite-production-at-8-billion-singapore-fab",
    "https://www.wikipedia.org/",
]

for url in urls:
    result = classify_page_access(url)
    print(result)
