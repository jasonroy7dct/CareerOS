from dataclasses import dataclass
from typing import Any
import requests

@dataclass
class GreenhouseSource:
    company: str
    board_token: str

def collect(source: GreenhouseSource, timeout: int = 20) -> list[dict[str, Any]]:
    response = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{source.board_token}/jobs?content=true", timeout=timeout)
    response.raise_for_status()
    return [{"company": source.company, "title": j.get("title", "").strip(), "location": (j.get("location") or {}).get("name", "").strip(), "url": j.get("absolute_url", "").strip(), "ats_id": str(j.get("id", "")), "posted_date": j.get("updated_at"), "description": j.get("content", ""), "source": "Greenhouse"} for j in response.json().get("jobs", [])]
