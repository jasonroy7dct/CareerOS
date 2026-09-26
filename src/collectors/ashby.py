from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests


@dataclass
class AshbySource:
    company: str
    board: str


def collect(source: AshbySource, timeout: int = 20) -> list[dict[str, Any]]:
    response = requests.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{source.board}",
        timeout=timeout,
    )
    response.raise_for_status()
    jobs: list[dict[str, Any]] = []
    for job in response.json().get("jobs", []):
        published_at = job.get("publishedAt")
        posted_date = None
        if isinstance(published_at, str):
            try:
                posted_date = datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                posted_date = None
        jobs.append({
            "company": source.company,
            "title": (job.get("title") or "").strip(),
            "location": (job.get("location") or "").strip(),
            "url": (job.get("jobUrl") or job.get("applyUrl") or "").strip(),
            "ats_id": str(job.get("id") or job.get("jobId") or ""),
            "posted_date": posted_date,
            "description": (job.get("descriptionHtml") or job.get("descriptionPlain") or "").strip(),
            "source": "Ashby",
        })
    return jobs
