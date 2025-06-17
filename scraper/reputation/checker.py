import os
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import dns.resolver
from bs4 import BeautifulSoup

load_dotenv()
SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_KEY")


# def get_external_links():
#     try:
#         response = requests.get("http://127.0.0.1:8000/risks")
#         response.raise_for_status()
#         return response.json()  # ✅ this gives you the list of dicts
#     except Exception as e:
#         return []

import time

API_KEY = "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"
VT_URL_REPORT = "https://www.virustotal.com/vtapi/v2/url/report"
VT_URL_SCAN = "https://www.virustotal.com/vtapi/v2/url/scan"


def get_url_report(target_url):
    params = {"apikey": API_KEY, "resource": target_url}
    try:
        r = requests.get(VT_URL_REPORT, params=params)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def submit_url_for_scan(target_url):
    data = {"apikey": API_KEY, "url": target_url}
    try:
        r = requests.post(VT_URL_SCAN, data=data)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_or_scan_url(target_url, wait_for_fresh=False):
    print(f"🔍 Checking existing VirusTotal scan for: {target_url}")
    report = get_url_report(target_url)

    if report.get("response_code") == 1:
        print(
            f"✅ Cached scan found. Detections: {report['positives']}/{report['total']}"
        )
        return report

    print("❌ No recent scan found. Submitting URL to VirusTotal...")
    scan_response = submit_url_for_scan(target_url)
    scan_id = scan_response.get("scan_id")

    if not wait_for_fresh:
        print("📤 URL submitted for scanning. Results will be available shortly.")
        return scan_response

    # Wait for scan results
    print("⏳ Waiting for scan to complete...")
    for i in range(10):
        time.sleep(10)
        report = get_url_report(target_url)
        if report.get("response_code") == 1:
            print(
                f"✅ Scan complete. Detections: {report['positives']}/{report['total']}"
            )
            return report
    print("⚠️ Timed out waiting for scan results.")
    return {"error": "Timed out"}


url = "https://www.xvideos.com/tags/xxxvideo"
get_or_scan_url(url, wait_for_fresh=True)


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
            # Grab the first threat type as the risk label
            threat_type = result["matches"][0].get("threatType", "malicious")
            return threat_type.lower()  # e.g., "malware", "unwanted_software"
        else:
            return "clean"
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return "error"


# main method in here
def analyze_links(scrapeID: int, url: str):

    try:
        risk_status = check_safe_browsing(url)

        # send to FastAPI server
        update_url = f"http://127.0.0.1:8000/updaterisk/{scrapeID}"
        response = requests.put(update_url, params={"status": risk_status})
        response.raise_for_status()

        print(f"SUCCESSFULLY Updated ID {scrapeID} with status: {risk_status}")

    except Exception as e:
        print(f"Failed to update {scrapeID} ({url}): {e}")


def contentFiltering(url):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ["1.1.1.3"]  # Cloudflare Family DNS

    try:
        answer = resolver.resolve(url, "A")
        # print(answer)
        # print(f"✅ {url} resolved — likely family-friendly.")
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        # print(f"🚫 {url} blocked by Cloudflare DNS — not family-friendly.")
        return False


# # Test
# print(contentFiltering("https://www.xvideos.com/tags/xxxvideo"))
# print(contentFiltering("https://optimaxaccess.iges.com/standard-gamble-sg/"))

# print(check_safe_browsing("https://www.xvideos.com/tags/pornhub"))
# print(check_safe_browsing("https://www.xvideos.com/tags/xxxvideo"))
# print(check_safe_browsing("https://optimaxaccess.iges.com/standard-gamble-sg/"))
