import asyncio
from scraper.crawler import run_crawler
from reputation.checker import analyze_links
from reportgenerator.report import generatePDF, send_email_with_report
import requests
from datetime import datetime, UTC
from collections import defaultdict
import pytz


def getAllCourseId():
    try:
        res = requests.get("http://127.0.0.1:8000/modules")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Failed to get module IDs: {e}")
        return []


def getRecentSessionScan():
    try:
        res = requests.get("http://127.0.0.1:8000/scrapedcontents/risks")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Failed to get module IDs: {e}")
        return []


def getAllHighRisks():
    try:
        res = requests.get("http://127.0.0.1:8000/scrapedcontents/highrisks")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Failed to get module IDs: {e}")
        return []


def startsession():
    payload = {
        "started_at": datetime.now(UTC).isoformat(),
        "completion_status": "running",
        "error_log": None,
    }
    try:
        res = requests.post(
            "http://127.0.0.1:8000/scrapersession/newsession", json=payload
        )
        res.raise_for_status()
        session_data = res.json()
        print(f"Scraper session created: {session_data['session_id']}")
        return session_data["session_id"]
    except Exception as e:
        print(f"Failed to create scraper session: {e}")
        return None


# async def batchScrape():
#     # get all courses list first
#     sessionId = startsession()
#     moduleIdList = getAllCourseId()
#     for module in moduleIdList:
#         moduleid = module["module_id"] + 1
#         # for my own local
#         # base_url = f"http://3.107.195.248/moodle/course/view.php?id={moduleid}"
#         # for vm
#         base_url = f"http://10.51.33.25/moodle/course/view.php?id={moduleid}"

#         print(base_url)
#         await run_crawler(base_url, sessionId, module["module_id"])


# testing only bsc203
async def batchScrape():
    # get all courses list first
    sessionId = startsession()

    moduleid = 2
    # for my own local
    # base_url = f"http://3.107.195.248/moodle/course/view.php?id={moduleid}"
    # for vm
    base_url = f"http://10.51.33.25/moodle/course/view.php?id={moduleid}"

    print(base_url)
    await run_crawler(base_url, sessionId, 2)


async def batchAnalyse():
    scans = getRecentSessionScan()
    print(scans)
    for scan in scans:
        print(scan)
        scrapeId = scan["scrapeID"]
        url = scan["url"]
        analyze_links(scrapeId, url)
    print(getRecentSessionScan())


async def batchReport():
    highRisks = getAllHighRisks()

    # Group links by module_id dynamically
    grouped_by_module = defaultdict(list)

    for item in highRisks:
        grouped_by_module[item["module_id"]].append(item)

    # Convert to regular dict (optional, e.g., if returning via API)
    grouped_by_module = dict(grouped_by_module)

    # ✅ Example usage: Print per-module grouped links
    for module_id, links in grouped_by_module.items():
        print(f"\n Module ID: {module_id} ({len(links)} links)")
        moduleInfo = requests.get(f"http://127.0.0.1:8000/modules/{module_id}").json()
        uc_id = moduleInfo["uc_id"]
        unitCoordinatorInfo = requests.get(
            f"http://127.0.0.1:8000/unitCoordinator/{uc_id}"
        ).json()
        unitCode = moduleInfo["unit_code"]
        unitCoordinatorName = unitCoordinatorInfo["full_name"]
        baseUrl = f"http://10.51.33.25//moodle/course/view.php?id={module_id+1}"
        report_path = generatePDF(unitCoordinatorName, unitCode, links, baseUrl)

        unitCoordinatorEmail = unitCoordinatorInfo["email"]
        send_email_with_report(
            unitCoordinatorEmail, report_path, unitCode, unitCoordinatorName
        )


async def main():
    await batchScrape()
    await batchAnalyse()
    await batchReport()


if __name__ == "__main__":
    asyncio.run(main())
