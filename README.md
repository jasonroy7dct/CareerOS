# CareerOS

CareerOS is a human-in-the-loop job-opportunity pipeline for technical-program-management roles. It reads official Greenhouse, Lever, and Ashby public job feeds, filters matching roles, deduplicates against the Notion **TPM Application Tracker**, and creates new records with `Status = Saved`. It never submits applications or changes an existing status.

## Setup

Under **Settings → Secrets and variables → Actions**, configure:

- Secret: `NOTION_TOKEN` — token from Notion **TPM Jobs Bot**.
- Variable: `NOTION_DATA_SOURCE_ID` — `40a0bcc9-1b61-40f6-b23d-c8c83713596e`.

Do not commit credentials.

## Source registry

`config/companies.json` is the source registry. Registry v1 contains verified public official-career feeds for OpenAI, Palantir, Zoox, Decagon, Zip, Valon, and Wayve. Sources are tagged `core_high_fit`, `large_tech`, or `growth` to support future ranking.

Supported ATS values:

- `greenhouse`: `board_token`
- `lever`: `site`
- `ashby`: `board`

Use only verified official ATS boards. Add sources incrementally, run a dry run, and inspect logs before enabling production writes.

## Schedule

The workflow runs weekdays at 7:00 AM Pacific during PDT (`0 14 * * 1-5`). GitHub cron uses UTC; change it to `0 15 * * 1-5` during PST. Use **Actions → Daily TPM Job Search → Run workflow** with `dry_run=true` before a production run.

## Dedupe

CareerOS skips a job when its canonical URL already exists in Notion, or when normalized `Company + Job Title + Location` already exists. It creates only new `Saved` records and leaves every existing Notion record unchanged.
