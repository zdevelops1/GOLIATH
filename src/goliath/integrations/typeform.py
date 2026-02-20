"""
Typeform Integration — manage forms, responses, and workspaces via the Typeform API.

SETUP INSTRUCTIONS
==================

1. Log in to Typeform at https://www.typeform.com/

2. Go to your account settings > Personal tokens
   (https://admin.typeform.com/account#/section/tokens).

3. Click "Generate a new token", select the scopes you need
   (forms:read, forms:write, responses:read, etc.).

4. Copy the token and add it to your .env:
     TYPEFORM_ACCESS_TOKEN=tfp_xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Authentication uses a Personal Access Token (Bearer).
- API docs: https://www.typeform.com/developers/
- Rate limit: 2 requests per second.
- Form IDs are found in the Typeform URL or via the API.
- Responses can be filtered by date, completion status, etc.

Usage:
    from goliath.integrations.typeform import TypeformClient

    tf = TypeformClient()

    # List forms
    forms = tf.list_forms()

    # Get a form
    form = tf.get_form("FORM_ID")

    # Get responses
    responses = tf.get_responses("FORM_ID", page_size=25)

    # Create a form
    form = tf.create_form(title="Customer Feedback")

    # Delete a form
    tf.delete_form("FORM_ID")

    # List workspaces
    workspaces = tf.list_workspaces()

    # Get form insights (response count, completion rate)
    insights = tf.get_form_insights("FORM_ID")
"""

import requests

from goliath import config

_API_BASE = "https://api.typeform.com"


class TypeformClient:
    """Typeform API client for forms, responses, and workspaces."""

    def __init__(self):
        if not config.TYPEFORM_ACCESS_TOKEN:
            raise RuntimeError(
                "TYPEFORM_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/typeform.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.TYPEFORM_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        })

    # -- Forms -------------------------------------------------------------

    def list_forms(self, page: int = 1, page_size: int = 10) -> list[dict]:
        """List forms.

        Args:
            page:      Page number.
            page_size: Results per page.

        Returns:
            List of form dicts.
        """
        return self._get(
            "/forms", params={"page": page, "page_size": page_size}
        ).get("items", [])

    def get_form(self, form_id: str) -> dict:
        """Get a form by ID.

        Args:
            form_id: Form ID.

        Returns:
            Form dict with title, fields, settings, etc.
        """
        return self._get(f"/forms/{form_id}")

    def create_form(self, title: str, fields: list[dict] | None = None, **kwargs) -> dict:
        """Create a new form.

        Args:
            title:  Form title.
            fields: List of field dicts (each with type, title, etc.).
            kwargs: Additional form settings.

        Returns:
            Created form dict.
        """
        data: dict = {"title": title, **kwargs}
        if fields:
            data["fields"] = fields
        return self._post("/forms", json=data)

    def update_form(self, form_id: str, **kwargs) -> dict:
        """Update a form.

        Args:
            form_id: Form ID.
            kwargs:  Fields to update (title, fields, settings, etc.).

        Returns:
            Updated form dict.
        """
        resp = self.session.put(f"{_API_BASE}/forms/{form_id}", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    def delete_form(self, form_id: str) -> None:
        """Delete a form.

        Args:
            form_id: Form ID.
        """
        resp = self.session.delete(f"{_API_BASE}/forms/{form_id}")
        resp.raise_for_status()

    # -- Responses ---------------------------------------------------------

    def get_responses(
        self,
        form_id: str,
        page_size: int = 25,
        since: str | None = None,
        until: str | None = None,
        completed: bool | None = None,
        **kwargs,
    ) -> dict:
        """Get responses for a form.

        Args:
            form_id:   Form ID.
            page_size: Results per page (max 1000).
            since:     ISO datetime to filter from.
            until:     ISO datetime to filter to.
            completed: Filter by completion status.
            kwargs:    Additional filters (after, before, sort, query, etc.).

        Returns:
            Dict with "items" (responses), "total_items", "page_count".
        """
        params: dict = {"page_size": page_size, **kwargs}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        if completed is not None:
            params["completed"] = str(completed).lower()
        return self._get(f"/forms/{form_id}/responses", params=params)

    def delete_responses(self, form_id: str, response_ids: list[str]) -> None:
        """Delete specific responses.

        Args:
            form_id:      Form ID.
            response_ids: List of response token IDs to delete.
        """
        params = {"included_tokens": ",".join(response_ids)}
        resp = self.session.delete(
            f"{_API_BASE}/forms/{form_id}/responses", params=params
        )
        resp.raise_for_status()

    # -- Insights ----------------------------------------------------------

    def get_form_insights(self, form_id: str) -> dict:
        """Get insights for a form (views, starts, completions).

        Args:
            form_id: Form ID.

        Returns:
            Insights dict.
        """
        return self._get(f"/insights/{form_id}/summary")

    # -- Workspaces --------------------------------------------------------

    def list_workspaces(self, page: int = 1, page_size: int = 10) -> list[dict]:
        """List workspaces.

        Args:
            page:      Page number.
            page_size: Results per page.

        Returns:
            List of workspace dicts.
        """
        return self._get(
            "/workspaces", params={"page": page, "page_size": page_size}
        ).get("items", [])

    def get_workspace(self, workspace_id: str) -> dict:
        """Get a workspace by ID.

        Args:
            workspace_id: Workspace ID.

        Returns:
            Workspace dict.
        """
        return self._get(f"/workspaces/{workspace_id}")

    # -- Themes ------------------------------------------------------------

    def list_themes(self, page: int = 1, page_size: int = 10) -> list[dict]:
        """List themes.

        Args:
            page:      Page number.
            page_size: Results per page.

        Returns:
            List of theme dicts.
        """
        return self._get(
            "/themes", params={"page": page, "page_size": page_size}
        ).get("items", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
