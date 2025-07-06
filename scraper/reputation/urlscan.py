import requests
import base64
import json
import os

VT_API_KEY = "0321311ce4e6139cf90dd29e3265b4299d6d0379d8178b3baeb90bcf49133f00"


def vt_v3_get_url_info(url):
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"

    headers = {"x-apikey": VT_API_KEY}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        data = response.json()
        stats = data["data"]["attributes"]["categories"]
        reputation =data["data"]["attributes"]["reputation"]
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


# ---------- Test ----------
if __name__ == "__main__":
    test_url = "http://xvideos.com/"
    report = vt_v3_get_url_info(test_url)
