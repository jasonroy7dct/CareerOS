from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import requests

@dataclass
class LeverSource:
    company: str
    site: str

def collect(source: LeverSource, timeout: int = 20) -> list[dict[str, Any]]:
    response = requests.get(f"https://api.lever.co/v0/postings/{source.site}?mode=json", timeout=timeout)
    response.raise_for_status()
    jobs = []
    for j in response.json():
        created = j.get("createdAt")
        posted_date = datetime.fromtimestamp(created / 1000, tz=timezone.utc).date().isoformat() if isinstance(created, (int, float)) else None
        jobs.append({"company": source.company, "title": (j.get("text") or "").strip(), "location": ((j.get("categories") or {}).get("location") or "").strip(), "url": (j.get("hostedUrl") or j.get("applyUrl") or "").strip(), "ats_id": str(j.get("id", "")), "posted_date": posted_date, "description": (j.get("descriptionPlain") or "").strip(), "source": "Lever"})
    return jobs
