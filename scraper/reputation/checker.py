import os
import time
import json
import requests
import dns.resolver
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import base64

# --------------------------------
# 🔐 API Keys & Config
# --------------------------------
load_dotenv(override=True)
VT_API_KEY = (
    os.getenv("VT_API_KEY")
    or "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"
)
SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_KEY")

VT_URL_REPORT = "https://www.virustotal.com/vtapi/v2/url/report"
VT_URL_SCAN = "https://www.virustotal.com/api/v3/urls"
VT_DOMAIN_REPORT = "https://www.virustotal.com/api/v3/domains/"


# --------------------------------
# 🔎 Utilities
# --------------------------------
def extract_domain_from_url(url: str) -> str:
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain[4:] if domain.startswith("www.") else domain
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return ""


# --------------------------------
# 🧪 VirusTotal Domain Scan (v3)
# --------------------------------
def get_report_given_domain(domain):
    headers = {"x-apikey": VT_API_KEY}
    response = requests.get(f"{VT_DOMAIN_REPORT}/{domain}", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Domain report failed with status code {response.status_code}")
        return None


def getscanresults(url):
    headers = {"x-apikey": VT_API_KEY}
    response = requests.get(f"{VT_URL_SCAN}/{url=}", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Domain report failed with status code {response.status_code}")
        return None


def getAnalysisOfExternalLinks(domain: str):
    reports_file = "scraper/reputation/output/reports.json"
    # report = get_report_given_domain(domain)
    report = getscanresults(domain)

    if not report:
        return None

    os.makedirs(os.path.dirname(reports_file), exist_ok=True)
    with open(reports_file, "w") as f:
        json.dump(report, f, indent=2)

    try:
        attributes = report["data"]["attributes"]
        domain = report["data"]["id"]
        reputation = attributes.get("reputation", "")
        categories = attributes.get("categories", {})
        category_values = ", ".join(categories.values())

        print("\n=== VirusTotal Analysis ===")
        print(f"Domain: {domain}")
        print(f"Reputation: {reputation}")
        print(f"Categories: {category_values}\n")

        return domain, reputation, category_values
    except Exception as e:
        print(f"❌ Error processing domain report: {e}")
        return None


# --------------------------------
# 🧪 VirusTotal URL Scan (v2)
# --------------------------------
def get_url_report(target_url):
    params = {"apikey": VT_API_KEY, "resource": target_url}
    try:
        return requests.get(VT_URL_REPORT, params=params).json()
    except Exception as e:
        return {"error": str(e)}


def submit_url_for_scan(target_url):
    data = {"apikey": VT_API_KEY, "url": target_url}
    try:
        return requests.post(VT_URL_SCAN, data=data).json()
    except Exception as e:
        return {"error": str(e)}


def get_or_scan_url(target_url, wait_for_fresh=False):
    print(f"🔍 Checking VirusTotal for: {target_url}")
    report = get_url_report(target_url)

    if report.get("response_code") == 1:
        print(f"✅ Cached: {report['positives']}/{report['total']} detections")
        return report

    print("❌ No cached report. Submitting for scan...")
    scan_response = submit_url_for_scan(target_url)

    if not wait_for_fresh:
        print("📤 Submitted. Results will be ready soon.")
        return scan_response

    print("⏳ Waiting for fresh scan...")
    for _ in range(10):
        time.sleep(10)
        report = get_url_report(target_url)
        if report.get("response_code") == 1:
            print(f"✅ Scan complete: {report['positives']}/{report['total']}")
            return report

    return {"error": "Timeout waiting for scan"}


# --------------------------------
# 🔐 Google Safe Browsing
# --------------------------------
def check_safe_browsing(url):
    payload = {
        "client": {"clientId": "lms-guardian", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
                "THREAT_TYPE_UNSPECIFIED",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        response = requests.post(
            f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={SAFE_BROWSING_API_KEY}",
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("matches"):
            return result["matches"][0].get("threatType", "malicious").lower()
        return "clean"
    except Exception as e:
        print(f"❌ Safe Browsing error: {e}")
        return "error"


def vt_v3_get_url_info(url):
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"

    headers = {"x-apikey": VT_API_KEY}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        data = response.json()
        stats = data["data"]["attributes"].get("categories", {})
        reputation = data["data"]["attributes"].get("reputation", 0)

        category_values = list(stats.values())
        categories = ", ".join(category_values)

        print(f"📊 reputation - {reputation}")
        print(f"🏷️ categories - {categories}")
        print(f"✅ Got report for {url}")
        return reputation, categories

    else:
        print(f"❌ Failed to get report: {response.status_code}")
        print(response.text)
        return None


VT_API_KEY = "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"


def vt_v3_get_url_info(url):
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"

    headers = {"x-apikey": VT_API_KEY}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        data = response.json()
        stats = data["data"]["attributes"]["categories"]
        reputation = data["data"]["attributes"]["reputation"]
        print(stats)
        category_values = list(stats.values())
        category_string = ", ".join(category_values)
        print(category_string)

        print(f"reputation - {reputation}")
        print(f"✅ Got report for {url}")
        return data
    else:
        print(f"❌ Failed to get report: {response.status_code}")
        print(response.text)
        return None


# --------------------------------
# 🧠 Main Risk Analysis
# --------------------------------
def analyze_links(scrapeID: int, url: str):
    try:
        result = vt_v3_get_url_info(url)

        # If not found, submit for scanning
        if result is None:
            print(f"📭 No report for {url}, submitting for scan...")
            scan_result = scan_url_v3(url)
            time.sleep(15)
            if scan_result:
                data = scan_result["data"]["attributes"]
                reputation = data.get("reputation", 0)
                categories = data.get("categories", {})
                category = ", ".join(categories.values())
            else:
                print(f"❌ Failed to retrieve scan result for {url}")
                return
        else:
            data = result["data"]["attributes"]
            reputation = data.get("reputation", 0)
            categories = data.get("categories", {})
            category = ", ".join(categories.values())

        # Update the local DB via FastAPI backend
        update_url = f"http://127.0.0.1:8000/scrapedcontents/updaterisk/{scrapeID}"
        response = requests.put(
            update_url, params={"score": reputation, "category": category}
        )
        response.raise_for_status()
        print(f"✅ Updated ID {scrapeID} → score={reputation}, category={category}")

    except Exception as e:
        print(f"❌ ERROR: Failed to update {scrapeID} ({url}) — {e}")


# --------------------------------
# 🧼 Content Filtering via DNS
# --------------------------------
def contentFiltering(url):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ["1.1.1.3"]  # Cloudflare Family DNS
    try:
        resolver.resolve(url, "A")
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return False


# --------------------------------
# 🧪 Test Section
# --------------------------------


def scan_url_v3(target_url):
    headers = {
        "x-apikey": VT_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = f"url={target_url}"
    scan_response = requests.post(VT_URL_SCAN, headers=headers, data=data)

    if scan_response.status_code != 200:
        print(f"❌ Failed to submit URL: {scan_response.status_code}")
        return None

    analysis_id = scan_response.json()["data"]["id"]
    print(f"📤 URL submitted. Analysis ID: {analysis_id}")

    # ✅ Correct endpoint for polling result
    analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"

    for i in range(10):
        time.sleep(10)
        report_response = requests.get(analysis_url, headers=headers)

        if report_response.status_code == 200:
            status = report_response.json()["data"]["attributes"]["status"]
            if status == "completed":
                print("✅ Scan complete.")
                return report_response.json()
            else:
                print(f"⏳ Still scanning... Attempt {i+1}/10")
        else:
            print(f"⚠️ Error fetching scan report: {report_response.status_code}")

    print("❌ Timed out waiting for scan result.")
    return None


def save_report_to_file(report, filename="output/url_scan_report.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"✅ Saved scan report to {filename}")


# if __name__ == "__main__":
# # Example usage
# url_to_scan = "https://www.example.com"  # Replace with your target URL
# result = scan_url_v3(url_to_scan)
# if result:
#     save_report_to_file(result)
# test_url = "https://www.xvideos.com/tags/xxxvideo"
# analyze_links(184, test_url)

# Other utilities:
# print(contentFiltering("www.xvideos.com"))
# print(check_safe_browsing("https://example.com"))
# print(get_or_scan_url("https://malicious.example", wait_for_fresh=True))
