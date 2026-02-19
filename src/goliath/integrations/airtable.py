"""
Airtable Integration — manage bases, tables, and records via the Airtable REST API.

SETUP INSTRUCTIONS
==================

1. Log in to https://airtable.com/

2. Go to https://airtable.com/create/tokens and create a personal access token.

3. Select the scopes you need:
   - data.records:read
   - data.records:write
   - schema.bases:read

4. Select which bases/workspaces the token can access.

5. Add to your .env:
     AIRTABLE_ACCESS_TOKEN=pat.xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Personal access tokens start with "pat.".
- Base IDs start with "app" (e.g. "appABC123def").
- Table names are case-sensitive. You can also use table IDs (start with "tbl").
- Record IDs start with "rec" (e.g. "recABC123def").
- Rate limit: 5 requests/second per base.
- Max 100 records per create/update call.
- API docs: https://airtable.com/developers/web/api/introduction

Usage:
    from goliath.integrations.airtable import AirtableClient

    at = AirtableClient()

    # List records
    records = at.list_records(base_id="appXXX", table="Tasks")

    # Create a record
    at.create_records(base_id="appXXX", table="Tasks", records=[
        {"fields": {"Name": "New task", "Status": "Todo"}}
    ])

    # Update a record
    at.update_records(base_id="appXXX", table="Tasks", records=[
        {"id": "recXXX", "fields": {"Status": "Done"}}
    ])

    # Delete records
    at.delete_records(base_id="appXXX", table="Tasks", record_ids=["recXXX"])
"""

import requests

from goliath import config

_API_BASE = "https://api.airtable.com/v0"


class AirtableClient:
    """Airtable REST API client for bases, tables, and records."""

    def __init__(self):
        if not config.AIRTABLE_ACCESS_TOKEN:
            raise RuntimeError(
                "AIRTABLE_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/airtable.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.AIRTABLE_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    # -- Records -----------------------------------------------------------

    def list_records(
        self,
        base_id: str,
        table: str,
        view: str | None = None,
        formula: str | None = None,
        max_records: int | None = None,
        sort: list[dict] | None = None,
    ) -> list[dict]:
        """List records in a table.

        Args:
            base_id:     Airtable base ID (e.g. "appXXX").
            table:       Table name or ID.
            view:        View name or ID to filter by.
            formula:     Airtable formula for filtering (e.g. "{Status}='Done'").
            max_records: Maximum number of records to return.
            sort:        Sort config (e.g. [{"field": "Name", "direction": "asc"}]).

        Returns:
            List of record dicts with id, fields, and createdTime.
        """
        params: dict = {}
        if view:
            params["view"] = view
        if formula:
            params["filterByFormula"] = formula
        if max_records:
            params["maxRecords"] = max_records
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")

        records = []
        while True:
            resp = self._get(f"/{base_id}/{table}", params=params)
            records.extend(resp.get("records", []))
            offset = resp.get("offset")
            if not offset:
                break
            params["offset"] = offset

        return records

    def get_record(self, base_id: str, table: str, record_id: str) -> dict:
        """Get a single record by ID.

        Args:
            base_id:   Airtable base ID.
            table:     Table name or ID.
            record_id: Record ID (e.g. "recXXX").

        Returns:
            Record dict.
        """
        return self._get(f"/{base_id}/{table}/{record_id}")

    def create_records(
        self, base_id: str, table: str, records: list[dict]
    ) -> list[dict]:
        """Create one or more records (max 10 per call).

        Args:
            base_id: Airtable base ID.
            table:   Table name or ID.
            records: List of dicts, each with a "fields" key.

        Returns:
            List of created record dicts.
        """
        resp = self._post(
            f"/{base_id}/{table}",
            json={"records": records},
        )
        return resp.get("records", [])

    def update_records(
        self, base_id: str, table: str, records: list[dict]
    ) -> list[dict]:
        """Update one or more records (max 10 per call).

        Args:
            base_id: Airtable base ID.
            table:   Table name or ID.
            records: List of dicts, each with "id" and "fields" keys.

        Returns:
            List of updated record dicts.
        """
        resp = self._patch(
            f"/{base_id}/{table}",
            json={"records": records},
        )
        return resp.get("records", [])

    def delete_records(
        self, base_id: str, table: str, record_ids: list[str]
    ) -> list[dict]:
        """Delete one or more records (max 10 per call).

        Args:
            base_id:    Airtable base ID.
            table:      Table name or ID.
            record_ids: List of record IDs to delete.

        Returns:
            List of deleted record confirmation dicts.
        """
        params = [("records[]", rid) for rid in record_ids]
        resp = self.session.delete(f"{_API_BASE}/{base_id}/{table}", params=params)
        resp.raise_for_status()
        return resp.json().get("records", [])

    # -- Bases -------------------------------------------------------------

    def list_bases(self) -> list[dict]:
        """List all accessible bases.

        Returns:
            List of base dicts with id and name.
        """
        resp = self.session.get(
            "https://api.airtable.com/v0/meta/bases",
            headers=self.session.headers,
        )
        resp.raise_for_status()
        return resp.json().get("bases", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, **kwargs) -> dict:
        resp = self.session.patch(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
