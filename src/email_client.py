import os
from datetime import date
from typing import Any

import requests

RESEND_API_URL = "https://api.resend.com/emails"


class EmailClient:
    """Sends a daily digest email via Resend after each job_search run."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("RESEND_API_KEY", "")
        self.to_email = os.environ.get("NOTIFY_EMAIL", "")
        # onboarding@resend.dev works out of the box with no domain
        # verification, but can only send to the Resend account owner's
        # own email. Once a sending domain is verified in Resend, set
        # FROM_EMAIL to something like "CareerOS <jobs@yourdomain.com>".
        self.from_email = os.environ.get("FROM_EMAIL", "CareerOS <onboarding@resend.dev>")
        self.enabled = bool(self.api_key and self.to_email)

    def _render_html(self, jobs: list[dict[str, Any]]) -> str:
        today = date.today().isoformat()
        if not jobs:
            body = "<p>No new matching TPM roles today.</p>"
        else:
            rows = "".join(
                f"<tr>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{j['priority']}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{j['company']}</td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>"
                f"<a href='{j['url']}'>{j['title']}</a></td>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{j.get('location','')}</td>"
                f"</tr>"
                for j in jobs
            )
            body = (
                "<table style='border-collapse:collapse;width:100%;font-family:sans-serif;font-size:14px'>"
                "<tr style='text-align:left;background:#f5f5f5'>"
                "<th style='padding:6px 10px'>Priority</th>"
                "<th style='padding:6px 10px'>Company</th>"
                "<th style='padding:6px 10px'>Role</th>"
                "<th style='padding:6px 10px'>Location</th>"
                "</tr>" + rows + "</table>"
            )
        return (
            f"<h2 style='font-family:sans-serif'>CareerOS — TPM jobs for {today}</h2>"
            f"{body}"
            "<p style='font-family:sans-serif;color:#888;font-size:12px'>"
            "New rows were also added to your Notion TPM Application Tracker with Status = Saved.</p>"
        )

    def send_digest(self, jobs: list[dict[str, Any]], dry_run: bool = False) -> None:
        if not self.enabled:
            print("Email skipped: RESEND_API_KEY or NOTIFY_EMAIL not set.")
            return
        if dry_run:
            print(f"[dry_run] Would email digest with {len(jobs)} job(s) to {self.to_email}.")
            return
        payload = {
            "from": self.from_email,
            "to": [self.to_email],
            "subject": f"CareerOS: {len(jobs)} new TPM role(s) — {date.today().isoformat()}",
            "html": self._render_html(jobs),
        }
        response = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
