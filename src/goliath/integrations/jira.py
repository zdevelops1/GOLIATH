"""
Jira Integration — manage issues, projects, and boards via the Jira Cloud REST API.

SETUP INSTRUCTIONS
==================

1. Log in to your Atlassian account at https://id.atlassian.com/

2. Go to https://id.atlassian.com/manage-profile/security/api-tokens

3. Click "Create API token", give it a label (e.g. "GOLIATH").

4. Copy the token.

5. Add to your .env:
     JIRA_URL=https://your-domain.atlassian.net
     JIRA_EMAIL=your-email@example.com
     JIRA_API_TOKEN=xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Authentication uses HTTP Basic (email + API token).
- The JIRA_URL must include the scheme (https://) and your subdomain.
- API docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Rate limit: ~100 requests/10 seconds per user.
- JQL (Jira Query Language) is used for searching issues.

Usage:
    from goliath.integrations.jira import JiraClient

    jira = JiraClient()

    # Create an issue
    issue = jira.create_issue(project="PROJ", summary="Bug report", issue_type="Bug")

    # Get an issue
    issue = jira.get_issue("PROJ-123")

    # Search issues with JQL
    results = jira.search("project = PROJ AND status = Open")

    # Add a comment
    jira.add_comment("PROJ-123", body="Working on this now.")

    # Transition an issue (e.g. move to "In Progress")
    jira.transition_issue("PROJ-123", transition_id="31")
"""

import requests

from goliath import config


class JiraClient:
    """Jira Cloud REST API client for issues, projects, and boards."""

    def __init__(self):
        if not config.JIRA_API_TOKEN:
            raise RuntimeError(
                "JIRA_API_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/jira.py for setup instructions."
            )
        if not config.JIRA_EMAIL:
            raise RuntimeError(
                "JIRA_EMAIL is not set. Add your Atlassian account email to .env."
            )
        if not config.JIRA_URL:
            raise RuntimeError(
                "JIRA_URL is not set (e.g. 'https://your-domain.atlassian.net'). "
                "Add it to .env or export as an environment variable."
            )

        self._base = config.JIRA_URL.rstrip("/") + "/rest/api/3"
        self.session = requests.Session()
        self.session.auth = (config.JIRA_EMAIL, config.JIRA_API_TOKEN)
        self.session.headers.update({"Content-Type": "application/json"})

    # -- Issues ------------------------------------------------------------

    def create_issue(
        self,
        project: str,
        summary: str,
        issue_type: str = "Task",
        description: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a new issue.

        Args:
            project:     Project key (e.g. "PROJ").
            summary:     Issue summary/title.
            issue_type:  Issue type name (Task, Bug, Story, Epic, etc.).
            description: Plain-text description (converted to ADF).
            kwargs:      Additional fields (priority, labels, assignee, etc.).

        Returns:
            Created issue dict with key, id, and self URL.
        """
        fields = {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
            **kwargs,
        }
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            }
        return self._post("/issue", json={"fields": fields})

    def get_issue(self, issue_key: str, fields: str | None = None) -> dict:
        """Get an issue by key.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            fields:    Comma-separated field names to return (None = all).

        Returns:
            Issue dict.
        """
        params = {}
        if fields:
            params["fields"] = fields
        return self._get(f"/issue/{issue_key}", params=params)

    def update_issue(self, issue_key: str, **kwargs) -> None:
        """Update an issue's fields.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            kwargs:    Fields to update (summary, description, priority, etc.).
        """
        resp = self.session.put(
            f"{self._base}/issue/{issue_key}",
            json={"fields": kwargs},
        )
        resp.raise_for_status()

    def delete_issue(self, issue_key: str) -> None:
        """Delete an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
        """
        resp = self.session.delete(f"{self._base}/issue/{issue_key}")
        resp.raise_for_status()

    def search(
        self, jql: str, max_results: int = 50, fields: str | None = None
    ) -> list[dict]:
        """Search issues using JQL.

        Args:
            jql:         Jira Query Language string.
            max_results: Maximum number of results.
            fields:      Comma-separated field names to return.

        Returns:
            List of issue dicts.
        """
        data: dict = {"jql": jql, "maxResults": max_results}
        if fields:
            data["fields"] = fields.split(",")
        resp = self._post("/search", json=data)
        return resp.get("issues", [])

    def assign_issue(self, issue_key: str, account_id: str) -> None:
        """Assign an issue to a user.

        Args:
            issue_key:  Issue key (e.g. "PROJ-123").
            account_id: Atlassian account ID of the assignee.
        """
        resp = self.session.put(
            f"{self._base}/issue/{issue_key}/assignee",
            json={"accountId": account_id},
        )
        resp.raise_for_status()

    # -- Transitions -------------------------------------------------------

    def get_transitions(self, issue_key: str) -> list[dict]:
        """Get available transitions for an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").

        Returns:
            List of transition dicts with id and name.
        """
        return self._get(f"/issue/{issue_key}/transitions").get("transitions", [])

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        """Transition an issue to a new status.

        Args:
            issue_key:     Issue key (e.g. "PROJ-123").
            transition_id: Transition ID (get from get_transitions()).
        """
        resp = self.session.post(
            f"{self._base}/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        resp.raise_for_status()

    # -- Comments ----------------------------------------------------------

    def add_comment(self, issue_key: str, body: str) -> dict:
        """Add a comment to an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            body:      Comment text (converted to ADF).

        Returns:
            Created comment dict.
        """
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": body}],
                }
            ],
        }
        return self._post(f"/issue/{issue_key}/comment", json={"body": adf_body})

    def get_comments(self, issue_key: str) -> list[dict]:
        """Get all comments on an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").

        Returns:
            List of comment dicts.
        """
        return self._get(f"/issue/{issue_key}/comment").get("comments", [])

    # -- Projects ----------------------------------------------------------

    def list_projects(self) -> list[dict]:
        """List all accessible projects.

        Returns:
            List of project dicts.
        """
        return self._get("/project")

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self._base}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
