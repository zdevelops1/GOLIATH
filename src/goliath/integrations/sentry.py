"""
Sentry Integration — manage projects, issues, and events via the Sentry REST API.

SETUP INSTRUCTIONS
==================

1. Log in to Sentry at https://sentry.io/

2. Go to Settings > Developer Settings > Internal Integrations
   (or https://sentry.io/settings/account/api/auth-tokens/).

3. Create a new auth token with the scopes you need:
   - project:read, project:write
   - org:read
   - event:read
   - issue:read, issue:write

4. Copy the token and add it to your .env:
     SENTRY_AUTH_TOKEN=sntrys_xxxxxxxxxxxxxxxx

5. Also set your organization slug:
     SENTRY_ORG=my-organization

IMPORTANT NOTES
===============
- API docs: https://docs.sentry.io/api/
- Rate limit: varies by endpoint.
- Base URL: https://sentry.io/api/0/ (or your self-hosted instance).

Usage:
    from goliath.integrations.sentry import SentryClient

    sentry = SentryClient()

    # List projects
    projects = sentry.list_projects()

    # List issues for a project
    issues = sentry.list_issues("my-project")

    # Get issue details
    issue = sentry.get_issue("12345")

    # Resolve an issue
    sentry.update_issue("12345", status="resolved")

    # List events for an issue
    events = sentry.list_issue_events("12345")

    # Get event details
    event = sentry.get_event("my-project", "event-id")
"""

import requests

from goliath import config

_DEFAULT_BASE = "https://sentry.io/api/0"


class SentryClient:
    """Sentry REST API client for projects, issues, and events."""

    def __init__(self):
        if not config.SENTRY_AUTH_TOKEN:
            raise RuntimeError(
                "SENTRY_AUTH_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/sentry.py for setup instructions."
            )

        self.org = config.SENTRY_ORG
        if not self.org:
            raise RuntimeError(
                "SENTRY_ORG is not set. "
                "Add it to .env (e.g. SENTRY_ORG=my-organization)."
            )

        self.base_url = (
            getattr(config, "SENTRY_BASE_URL", "") or _DEFAULT_BASE
        )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.SENTRY_AUTH_TOKEN}",
            "Content-Type": "application/json",
        })

    # -- Projects --------------------------------------------------------------

    def list_projects(self) -> list[dict]:
        """List all projects in the organization.

        Returns:
            List of project dicts.
        """
        return self._get(f"/organizations/{self.org}/projects/")

    def get_project(self, project_slug: str) -> dict:
        """Get project details.

        Args:
            project_slug: Project slug.

        Returns:
            Project dict.
        """
        return self._get_single(f"/projects/{self.org}/{project_slug}/")

    # -- Issues ----------------------------------------------------------------

    def list_issues(
        self,
        project_slug: str,
        query: str = "",
        sort: str = "date",
        limit: int = 25,
    ) -> list[dict]:
        """List issues for a project.

        Args:
            project_slug: Project slug.
            query:        Sentry search query (e.g. "is:unresolved").
            sort:         Sort order ("date", "new", "priority", "freq").
            limit:        Max results.

        Returns:
            List of issue dicts.
        """
        params: dict = {"sort": sort, "limit": limit}
        if query:
            params["query"] = query
        return self._get(
            f"/projects/{self.org}/{project_slug}/issues/", params=params
        )

    def get_issue(self, issue_id: str) -> dict:
        """Get issue details.

        Args:
            issue_id: Issue ID.

        Returns:
            Issue dict.
        """
        return self._get_single(f"/issues/{issue_id}/")

    def update_issue(self, issue_id: str, **kwargs) -> dict:
        """Update an issue (resolve, ignore, assign, etc.).

        Args:
            issue_id: Issue ID.
            kwargs:   Fields to update (status, assignedTo, hasSeen, isBookmarked).

        Returns:
            Updated issue dict.
        """
        resp = self.session.put(
            f"{self.base_url}/issues/{issue_id}/", json=kwargs
        )
        resp.raise_for_status()
        return resp.json()

    def delete_issue(self, issue_id: str) -> dict:
        """Delete an issue.

        Args:
            issue_id: Issue ID.

        Returns:
            Deletion result.
        """
        resp = self.session.delete(f"{self.base_url}/issues/{issue_id}/")
        resp.raise_for_status()
        return {"status": "deleted"}

    # -- Events ----------------------------------------------------------------

    def list_issue_events(self, issue_id: str, limit: int = 25) -> list[dict]:
        """List events for an issue.

        Args:
            issue_id: Issue ID.
            limit:    Max results.

        Returns:
            List of event dicts.
        """
        return self._get(
            f"/issues/{issue_id}/events/", params={"limit": limit}
        )

    def get_event(self, project_slug: str, event_id: str) -> dict:
        """Get event details.

        Args:
            project_slug: Project slug.
            event_id:     Event ID.

        Returns:
            Event dict.
        """
        return self._get_single(
            f"/projects/{self.org}/{project_slug}/events/{event_id}/"
        )

    # -- Tags & Stats ---------------------------------------------------------

    def list_tags(self, issue_id: str) -> list[dict]:
        """List tags for an issue.

        Args:
            issue_id: Issue ID.

        Returns:
            List of tag dicts.
        """
        return self._get(f"/issues/{issue_id}/tags/")

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> list[dict]:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _get_single(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
