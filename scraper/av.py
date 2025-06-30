import subprocess


def scan_file_with_clamav(file_path: str) -> bool:
    try:
        result = subprocess.run(
            ["clamscan", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        print(result.stdout)
        if "Infected files: 0" in result.stdout:
            return True  # Clean
        else:
            return False  # Infected

    except Exception as e:
        print(f"❌ Error running ClamAV: {e}")
        return False


import requests


def check_urlhaus(url: str):
    try:
        response = requests.post(
            "https://urlhaus-api.abuse.ch/v1/url/",
            data={"url": url},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("query_status") != "no_results"
        else:
            print(f"❌ URLhaus error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Failed to check URLhaus: {e}")
        return False


malicious = "https://www.xvideos.com"
clean = "https://example.org/safe"

print("Malicious URL:", check_urlhaus(malicious))  # True
print("Clean URL:", check_urlhaus(clean))  # False
import requests
import base64


def encode_url_for_vt(url):
    b64 = base64.urlsafe_b64encode(url.encode()).decode()
    return b64.strip("=")


def get_vt_vendor_verdicts(api_key, url):
    encoded_url = encode_url_for_vt(url)
    domain = requests.utils.urlparse(url).netloc

    headers = {"x-apikey": api_key}

    vt_url = f"https://www.virustotal.com/api/v3/urls/{encoded_url}"
    vt_domain = f"https://www.virustotal.com/api/v3/domains/{domain}"

    response_url = requests.get(vt_url, headers=headers)
    response_domain = requests.get(vt_domain, headers=headers)

    data_url = response_url.json()
    data_domain = response_domain.json()

    print("===== URL Analysis =====")
    print(data_url)
    print("===== Domain Analysis =====")
    print(data_domain)

    return {"url": data_url, "domain": data_domain}


api = "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"
get_vt_vendor_verdicts(api, malicious)
