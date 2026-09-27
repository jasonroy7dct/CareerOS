import html
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dateutil.parser import parse as parse_date

from src.collectors.ashby import AshbySource, collect as ashby
from src.collectors.greenhouse import GreenhouseSource, collect as greenhouse
from src.collectors.lever import LeverSource, collect as lever
from src.email_client import EmailClient
from src.notion_client import NotionClient

ROOT = Path(__file__).resolve().parents[1]

def load(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text())

def norm(x: str | None) -> str:
    return re.sub(r"\s+", " ", (x or "").strip().casefold())

def canon(url: str | None) -> str:
    if not url:
        return ""
    p = urlsplit(url.strip())
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith(("utm_", "gh_", "lever-"))]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urlencode(q), ""))

def text(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    if prop.get("type") == "url":
        return prop.get("url") or ""
    key = "title" if prop.get("type") == "title" else "rich_text"
    return "".join(x.get("plain_text", "") for x in prop.get(key, []))

def keys(rows: list[dict[str, Any]]) -> tuple[set[str], set[tuple[str, str, str]]]:
    urls, triples = set(), set()
    for row in rows:
        p = row.get("properties", {})
        u = canon(text(p.get("Job URL")))
        if u:
            urls.add(u)
        triples.add((norm(text(p.get("Company"))), norm(text(p.get("Job Title"))), norm(text(p.get("Location")))))
    return urls, triples

def safe_date(x: str | None) -> str | None:
    try:
        return parse_date(x).date().isoformat() if x else None
    except (TypeError, ValueError, OverflowError):
        return None

def clean(x: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x or ""))).strip()

def match(job: dict[str, Any], rules: dict[str, Any]) -> bool:
    title, location = norm(job.get("title")), norm(job.get("location"))
    return bool(
        title
        and job.get("url")
        and not any(x in title for x in rules["exclude_title_keywords"])
        and any(x in title for x in rules["include_title_keywords"])
        and (not location or any(x in location for x in rules["location_keywords"]))
    )

def priority(job: dict[str, Any], rules: dict[str, Any]) -> str:
    h = norm(f"{job.get('title', '')} {job.get('description', '')}")
    if any(x in h for x in rules["priority_keywords"]["High"]):
        return "High"
    if any(x in h for x in rules["priority_keywords"]["Medium"]):
        return "Medium"
    return "Low"

def collect(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    out, skipped = [], []
    for c in config.get("companies", []):
        ats = c.get("ats", "").lower()
        try:
            if ats == "greenhouse" and c.get("board_token"):
                out += greenhouse(GreenhouseSource(c["name"], c["board_token"]))
            elif ats == "lever" and c.get("site"):
                out += lever(LeverSource(c["name"], c["site"]))
            elif ats == "ashby" and c.get("board"):
                out += ashby(AshbySource(c["name"], c["board"]))
            else:
                skipped.append(c.get("name", "unknown"))
        except Exception as e:
            print(f"Collector failed for {c.get('name', 'unknown')}: {e}")
            skipped.append(c.get("name", "unknown"))
    return out, skipped

def main() -> None:
    rules, config, client = load("config/search_rules.json"), load("config/companies.json"), NotionClient()
    urls, triples = keys(client.existing_records())
    limit = int(os.environ.get("MAX_NEW_JOBS", rules["max_new_jobs"]))
    dry = os.environ.get("DRY_RUN", "false").lower() == "true"
    jobs, skipped = collect(config)
    if skipped:
        print(f"WARNING: {len(skipped)} companies were NOT collected (missing/unrecognized ats info): {', '.join(skipped)}")
    found = []
    for j in jobs:
        j["url"], j["description"], j["posted_date"] = canon(j.get("url")), clean(j.get("description")), safe_date(j.get("posted_date"))
        triple = (norm(j.get("company")), norm(j.get("title")), norm(j.get("location")))
        if not match(j, rules) or j["url"] in urls or triple in triples:
            continue
        j["priority"], j["found_date"] = priority(j, rules), date.today().isoformat()
        found.append(j)
        urls.add(j["url"])
        triples.add(triple)
        if len(found) >= limit:
            break
    print(f"Found {len(found)} new matching jobs. dry_run={dry}")
    for j in found:
        print(f"[{j['priority']}] {j['company']} — {j['title']} — {j['location']}")
        if not dry:
            client.create_job(j)
    EmailClient().send_digest(found, dry_run=dry, skipped=skipped)

if __name__ == "__main__":
    main()
