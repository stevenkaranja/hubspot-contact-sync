# HubSpot Contact Sync

Sync contacts from Google Sheets (or CSV) into HubSpot with deduplication, field mapping, and upsert logic.

No more manual copy-paste between spreadsheets and your CRM. This tool reads your lead list, maps columns to HubSpot properties, deduplicates by email, and syncs everything in one command.

---

## What It Does

```
Input: Google Sheet or CSV
         ↓
  [Read + Normalise]     — strip whitespace, lowercase emails, drop blanks
         ↓
  [Field Mapping]        — sheet columns → HubSpot property names
         ↓
  [Dedup Check]          — look up each email in HubSpot
         ↓
  [Upsert]               — create if new, update if exists
         ↓
Output: HubSpot CRM updated + sync_log.csv
```

---

## Stack

| Layer | Tool |
|---|---|
| CRM | HubSpot v3 Contacts API |
| Sheet reading | gspread + Google Sheets API |
| Data processing | pandas |
| CLI | rich |

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/stevenkaranja/hubspot-contact-sync
cd hubspot-contact-sync

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Add your HubSpot private app token

# 4. Dry run first (preview without writing)
python main.py --csv data/sample_contacts.csv --dry-run

# 5. Run for real
python main.py --csv data/sample_contacts.csv

# 6. Sync from Google Sheets
python main.py --sheet YOUR_SHEET_ID
```

---

## Input Format

CSV or Google Sheet with any of these columns (extra columns are ignored):

| Column | HubSpot Property |
|---|---|
| `email` | email *(required)* |
| `first_name` | firstname |
| `last_name` | lastname |
| `company` | company |
| `job_title` | jobtitle |
| `phone` | phone |
| `country` | country |
| `lead_source` | hs_lead_status |

---

## Sync Modes

| Mode | Behaviour |
|---|---|
| `upsert` *(default)* | Create new + update existing |
| `create_only` | Skip contacts that already exist |
| `update_only` | Only update existing contacts |

```bash
python main.py --csv leads.csv --mode create_only
```

---

## Output

After each run a `sync_log_YYYYMMDD_HHMMSS.csv` is saved with:

| Field | Description |
|---|---|
| `email` | Contact email |
| `action` | created / updated / skipped / error |
| `id` | HubSpot contact ID |
| `reason` | Error message if failed |

---

## HubSpot Setup

1. Go to **HubSpot → Settings → Integrations → Private Apps**
2. Create a new app with scopes: `crm.objects.contacts.read` + `crm.objects.contacts.write`
3. Copy the token → add to `.env` as `HUBSPOT_API_KEY`

---

## Author

**Stephen Karanja** — AI Automation & GTM Systems Engineer  
[stephenkaranja.vercel.app](https://stephenkaranja.vercel.app) · [LinkedIn](https://linkedin.com/in/steven-karanja)
