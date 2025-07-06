import requests
import base64
import json
import time
import os

VT_API_KEY = "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"
SCAN_URL = "https://www.virustotal.com/api/v3/urls"
GET_ANALYSIS = "https://www.virustotal.com/api/v3/analyses/"


def vt_v3_scan_url(url_to_scan):
    headers = {
        "x-apikey": VT_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = f"url={url_to_scan}"
    response = requests.post(SCAN_URL, headers=headers, data=data)

    if response.status_code != 200:
        print(f"❌ Failed to submit URL: {response.status_code}")
        print(response.text)
        return None

    analysis_id = response.json()["data"]["id"]
    print(f"📤 URL submitted, analysis ID: {analysis_id}")
    return analysis_id


def vt_v3_get_report(analysis_id):
    headers = {"x-apikey": VT_API_KEY}

    for i in range(10):
        time.sleep(5)
        response = requests.get(f"{GET_ANALYSIS}{analysis_id}", headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data["data"]["attributes"]["status"] == "completed":
                print("✅ Scan complete.")
                return data
            else:
                print(f"⏳ Scan in progress... ({i+1}/10)")
        else:
            print(f"⚠️ Error fetching report: {response.status_code}")
            break

    print("❌ Timed out waiting for results.")
    return None


def save_report_to_json(report, filename="output/url_scan_v3.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"✅ Report saved to {filename}")


# ---------- Test ----------
if __name__ == "__main__":
    url = "http://xvideos.com/"
    analysis_id = vt_v3_scan_url(url)

    if analysis_id:
        report = vt_v3_get_report(analysis_id)
        if report:
            save_report_to_json(report)
