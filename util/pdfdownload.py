import os
import aiohttp
from urllib.parse import urlsplit

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def download_file(session: aiohttp.ClientSession, url: str):
    filename = os.path.basename(urlsplit(url).path)
    local_path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(local_path):
        print(f"[SKIP] Already downloaded: {filename}")
        return

    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(local_path, "wb") as f:
                    f.write(await resp.read())
                print(f"[DOWNLOAD] Saved: {filename}")
            else:
                print(f"[ERROR] Failed to download {url} (Status {resp.status})")
    except Exception as e:
        print(f"[ERROR] Exception downloading {url}: {e}")
