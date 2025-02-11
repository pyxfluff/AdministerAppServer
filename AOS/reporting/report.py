# pyxfluff 2024

# NOT FOR PUBLIC RELEASE

import src

from time import time
from json import dumps
from httpx import post
from datetime import datetime

def posneg_str(value, value2) -> str:
    return f"{(value > value2) and "+" or ""}{value-value2}"

def daily_report(
        database,
) -> None:
    day = round(time() / 86400) - 1
    st = time()
    yesterday_report = database.get(f"day-{day}", database.REPORTED_VERSIONS)

    print(dumps(database.get(day + 1, database.REPORTED_VERSIONS)))

    if not yesterday_report:
        yesterday_report = {
            "places_len": 0,
            "api_requests": 0,
            "app_downloads": 0,
            "app_votes": 0,
            "ip_blocks": 0
        }

    todays_report = {
        "places_len": len(database.get_all(database.PLACES)),
        "api_requests": src.requests,
        "app_downloads": src.downloads_today,
        "app_votes": 0,
        "ip_blocks": 0
    }

    if database.get(day, database.REPORTED_VERSIONS) == None:
        database.set(day, {"internal": {},"qa": {},"canary": {},"beta": {},"live": {}}, database.REPORTED_VERSIONS)

    database.set(f"day-{round(time() / 86400)}", todays_report, database.REPORTED_VERSIONS)

    post(
        url = "https://discord.com/api/webhooks/1299120437984497695/IYGS0-Dsh2Rkw24K5w6XnofIzroIEmp_pndhdGGz0EfsdHvBr5xydt2tnMNJYjz_eRNw",
        json = {
            "content": f"Here is your report for **day {day}**",
            "embeds": [
                {
                    "title": "Statistics",
                    "description": f"""
                    ```yaml
- New places: ({len(database.get_all(database.PLACES)) - yesterday_report["places_len"]}) ({posneg_str(len(database.get_all(database.PLACES)), yesterday_report["places_len"])}, {len(database.get_all(database.PLACES))} in total)
- Total API Requests: {src.requests} ({posneg_str(src.requests, yesterday_report["api_requests"])})
- Stable branch usage: {dumps(database.get(day, database.REPORTED_VERSIONS)["live"])} (yesterday: {dumps(database.get(day - 1, database.REPORTED_VERSIONS)["live"])})
- App downloads: {src.downloads_today} ({posneg_str(src.downloads_today, yesterday_report["app_downloads"])})
- App votes: 0 (+0)
- Automated IP blocks: 0 (-0)```""".strip(),
                    "color": 5814783,
                    "footer": {
                        "text": f"Report processed and generated in {time() - st}s"
                    },
                    "timestamp": datetime.now().isoformat(timespec='milliseconds') + 'Z',
                },
            ],
            "username": "Administer Reporting",
            "attachments": []
        }
    )

    src.downloads_today = 0
    src.requests = 0
