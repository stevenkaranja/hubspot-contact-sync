"""
HubSpot CRM client — create, update, and upsert contacts.
Uses HubSpot v3 Contacts API.
"""
import os
import time
import requests


HUBSPOT_BASE = "https://api.hubapi.com"

# Map sheet column names → HubSpot property names
FIELD_MAP = {
    "email": "email",
    "first_name": "firstname",
    "last_name": "lastname",
    "phone": "phone",
    "company": "company",
    "job_title": "jobtitle",
    "website": "website",
    "city": "city",
    "country": "country",
    "linkedin_url": "hs_linkedin_url",
    "lead_source": "hs_lead_status",
    "notes": "hs_content_membership_notes",
}


class HubSpotClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY", "")
        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY is required")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.rate_limit_delay = 0.12  # ~8 req/sec (well under 100/10s limit)

    def _map_properties(self, row: dict) -> dict:
        """Map sheet columns to HubSpot properties."""
        props = {}
        for sheet_col, hs_prop in FIELD_MAP.items():
            val = row.get(sheet_col, "")
            if val and str(val).strip():
                props[hs_prop] = str(val).strip()
        return props

    def get_contact_by_email(self, email: str) -> dict | None:
        """Look up an existing contact by email."""
        resp = requests.get(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{email}",
            params={"idProperty": "email", "properties": "email,firstname,lastname"},
            headers=self.headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        return None

    def create_contact(self, row: dict) -> dict:
        """Create a new contact."""
        props = self._map_properties(row)
        resp = requests.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
            json={"properties": props},
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def update_contact(self, contact_id: str, row: dict) -> dict:
        """Update an existing contact by ID."""
        props = self._map_properties(row)
        resp = requests.patch(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
            json={"properties": props},
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def upsert(self, row: dict) -> tuple[str, str]:
        """
        Upsert a contact (create if new, update if exists).
        Returns: (action, contact_id) where action is 'created' or 'updated'
        """
        time.sleep(self.rate_limit_delay)
        email = row.get("email", "")
        existing = self.get_contact_by_email(email)

        if existing:
            contact_id = existing["id"]
            self.update_contact(contact_id, row)
            return "updated", contact_id
        else:
            created = self.create_contact(row)
            return "created", created["id"]

    def batch_upsert(self, rows: list[dict], dry_run: bool = False) -> list[dict]:
        """
        Upsert a batch of contacts with result tracking.
        Returns a list of result dicts.
        """
        results = []
        for row in rows:
            email = row.get("email", "")
            if not email:
                results.append({"email": "—", "action": "skipped", "reason": "no email", "id": ""})
                continue
            try:
                if dry_run:
                    existing = self.get_contact_by_email(email)
                    action = "would_update" if existing else "would_create"
                    results.append({"email": email, "action": action, "reason": "", "id": ""})
                else:
                    action, contact_id = self.upsert(row)
                    results.append({"email": email, "action": action, "reason": "", "id": contact_id})
            except Exception as e:
                results.append({"email": email, "action": "error", "reason": str(e), "id": ""})
        return results
