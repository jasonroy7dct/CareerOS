import os
from typing import Any
import requests

NOTION_VERSION = "2025-09-03"

class NotionClient:
    def __init__(self) -> None:
        self.token = os.environ.get("NOTION_TOKEN", "")
        self.data_source_id = os.environ.get("NOTION_DATA_SOURCE_ID", "")
        if not self.token or not self.data_source_id:
            raise RuntimeError("Set NOTION_TOKEN secret and NOTION_DATA_SOURCE_ID variable.")
        self.headers = {"Authorization": f"Bearer {self.token}", "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}

    def existing_records(self) -> list[dict[str, Any]]:
        rows, cursor = [], None
        while True:
            body = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            response = requests.post(f"https://api.notion.com/v1/data_sources/{self.data_source_id}/query", headers=self.headers, json=body, timeout=30)
            response.raise_for_status()
            payload = response.json()
            rows.extend(payload.get("results", []))
            if not payload.get("has_more"):
                return rows
            cursor = payload.get("next_cursor")

    def create_job(self, job: dict[str, Any]) -> None:
        p = {"Job Title": {"title": [{"text": {"content": job["title"]}}]}, "Company": {"rich_text": [{"text": {"content": job["company"]}}]}, "Status": {"select": {"name": "Saved"}}, "Found Date": {"date": {"start": job["found_date"]}}, "Job URL": {"url": job["url"]}, "Source": {"rich_text": [{"text": {"content": job["source"]}}]}, "Location": {"rich_text": [{"text": {"content": job["location"]}}]}, "Priority": {"select": {"name": job["priority"]}}, "Description": {"rich_text": [{"text": {"content": job["description"][:1900]}}]}}
        if job.get("posted_date"):
            p["Posted Date"] = {"date": {"start": job["posted_date"]}}
        response = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json={"parent": {"type": "data_source_id", "data_source_id": self.data_source_id}, "properties": p}, timeout=30)
        response.raise_for_status()
