import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import os
import requests
import json
from urllib.parse import urlparse


def extract_domain_from_url(url: str) -> str:
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url  # Default to http if no scheme
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return ""


# print("gogo")
# print(extract_domain_from_url("www.pornhub.com/videos"))  # Output: pornhub.com


API = "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"  # Replace with your API key


def get_report_given_domain(domain):
    base_url = "https://www.virustotal.com/api/v3/domains/"
    headers = {"x-apikey": API}

    formatted_url = f"{base_url}/{domain}"
    response = requests.get(formatted_url, headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        return json_response
    else:
        print(f"❌ Request failed with status code {response.status_code}")
        return None


def getAnalysisOfExternalLinks(domain: str):
    reports_file = "output/reports.json"  # Ensure this directory exists

    # Fetch report
    report = get_report_given_domain(domain)
    if not report:
        return None

    # Save raw JSON to file
    os.makedirs(os.path.dirname(reports_file), exist_ok=True)
    with open(reports_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Saved report to {reports_file}")

    # Extract and print summary
    print("\ndomain,reputation,categories")
    try:
        attributes = report["data"]["attributes"]
        domain = report["data"]["id"]
        reputation = attributes.get("reputation", "")
        categories = attributes.get("categories", {})
        category_values = ", ".join(categories.values())

        print("=== Analysis ===")
        print(f"Domain - {domain}")
        print(f"Reputation score - {reputation}")
        print(f"Category - {category_values}")
        print(f"{domain},{reputation},{category_values}\n")
        return domain, reputation, category_values

    except Exception as e:
        print(f"❌ Error processing the report: {e}")
        return None


# domain_to_check = "pornhub.com"  # Change this to your target domain
# a, b, c = getAnalysisOfExternalLinks(domain_to_check)
# print(f"a = {a}")
# print(f"b = {b}")
# print(f"c = {c}")


load_dotenv(override=True)
SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_KEY")


# def get_external_links():
#     try:
#         response = requests.get("http://127.0.0.1:8000/risks")
#         response.raise_for_status()
#         return response.json()  # ✅ this gives you the list of dicts
#     except Exception as e:
#         return []


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


# url = "https://www.xvideos.com/tags/xxxvideo"
# get_or_scan_url(url, wait_for_fresh=True)


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
        # Extract domain and run external risk analysis
        domainOfURL = extract_domain_from_url(url)
        print(f"Extracted domain: {domainOfURL}")

        domain, score, category = getAnalysisOfExternalLinks(
            domainOfURL
        )  # e.g., "example.com", 0.85, "malware"

        # Send to FastAPI server with separate risk_score and risk_category
        update_url = f"http://127.0.0.1:8000/updaterisk/{scrapeID}"
        response = requests.put(
            update_url, params={"score": score, "category": category}
        )
        response.raise_for_status()

        print(
            f"✅ SUCCESS: Updated ID {scrapeID} with score={score}, category={category}"
        )

    except Exception as e:
        print(f"❌ ERROR: Failed to update {scrapeID} ({url}) — {e}")


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
