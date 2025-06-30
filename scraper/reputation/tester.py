import requests
from bs4 import BeautifulSoup

def check_opendns_category(domain):
    url = f"https://domain.opendns.com/{domain}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    categories = soup.select("div#tag-wrapper a")
    tags = [tag.text.strip() for tag in categories]

    if tags:
        print(f"🔎 Categories for {domain}: {', '.join(tags)}")
        return tags
    else:
        print(f"⚠️ No categories found for {domain}. Might be uncategorized.")
        return []

# Example usage
check_opendns_category("xvideos.com")
