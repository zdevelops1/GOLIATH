"""
Linear Integration — manage issues, projects, and teams via the Linear GraphQL API.

SETUP INSTRUCTIONS
==================

1. Log in to Linear at https://linear.app/

2. Go to Settings > API (or visit https://linear.app/settings/api).

3. Under "Personal API keys", click "Create key".

4. Copy the key and add it to your .env:
     LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Linear uses a GraphQL API (single endpoint).
- Authentication uses a Bearer token.
- API docs: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- Rate limit: 1500 requests per hour per key.
- All queries go through: https://api.linear.app/graphql

Usage:
    from goliath.integrations.linear import LinearClient

    lin = LinearClient()

    # List issues assigned to me
    issues = lin.list_my_issues()

    # Get an issue by identifier (e.g. "ENG-123")
    issue = lin.get_issue("ISSUE_UUID")

    # Create an issue
    issue = lin.create_issue(
        team_id="TEAM_UUID",
        title="Fix login bug",
        description="Users report 403 on the login page.",
        priority=2,
    )

    # Update an issue
    lin.update_issue("ISSUE_UUID", state_id="STATE_UUID")

    # List teams
    teams = lin.list_teams()

    # List projects
    projects = lin.list_projects()

    # Search issues
    results = lin.search_issues("login bug")

    # Add a comment to an issue
    lin.add_comment("ISSUE_UUID", body="Investigating now.")
"""

import requests

from goliath import config

_API_URL = "https://api.linear.app/graphql"


class LinearClient:
    """Linear GraphQL API client for issues, projects, and teams."""

    def __init__(self):
        if not config.LINEAR_API_KEY:
            raise RuntimeError(
                "LINEAR_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/linear.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": config.LINEAR_API_KEY,
            "Content-Type": "application/json",
        })

    # -- Issues ------------------------------------------------------------

    def list_my_issues(self, first: int = 50) -> list[dict]:
        """List issues assigned to the authenticated user.

        Args:
            first: Max results.

        Returns:
            List of issue dicts.
        """
        query = """
        query($first: Int!) {
          viewer {
            assignedIssues(first: $first, orderBy: updatedAt) {
              nodes { id identifier title state { name } priority priorityLabel
                      assignee { name } createdAt updatedAt }
            }
          }
        }
        """
        data = self._query(query, {"first": first})
        return data.get("viewer", {}).get("assignedIssues", {}).get("nodes", [])

    def get_issue(self, issue_id: str) -> dict:
        """Get an issue by UUID.

        Args:
            issue_id: Issue UUID.

        Returns:
            Issue dict.
        """
        query = """
        query($id: String!) {
          issue(id: $id) {
            id identifier title description state { id name }
            priority priorityLabel assignee { id name }
            project { id name } team { id name key }
            labels { nodes { id name } }
            createdAt updatedAt
          }
        }
        """
        return self._query(query, {"id": issue_id}).get("issue", {})

    def create_issue(
        self,
        team_id: str,
        title: str,
        description: str = "",
        priority: int | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
        state_id: str | None = None,
        label_ids: list[str] | None = None,
    ) -> dict:
        """Create an issue.

        Args:
            team_id:     Team UUID.
            title:       Issue title.
            description: Markdown description.
            priority:    Priority (0=none, 1=urgent, 2=high, 3=medium, 4=low).
            assignee_id: Assignee user UUID.
            project_id:  Project UUID.
            state_id:    Workflow state UUID.
            label_ids:   List of label UUIDs.

        Returns:
            Dict with "success" and created "issue".
        """
        input_fields = f'teamId: "{team_id}", title: "{_esc(title)}"'
        if description:
            input_fields += f', description: "{_esc(description)}"'
        if priority is not None:
            input_fields += f", priority: {priority}"
        if assignee_id:
            input_fields += f', assigneeId: "{assignee_id}"'
        if project_id:
            input_fields += f', projectId: "{project_id}"'
        if state_id:
            input_fields += f', stateId: "{state_id}"'
        if label_ids:
            ids_str = ", ".join(f'"{lid}"' for lid in label_ids)
            input_fields += f", labelIds: [{ids_str}]"

        query = (
            "mutation { issueCreate(input: {%s}) { success issue "
            "{ id identifier title state { name } priority } } }" % input_fields
        )
        return self._query(query).get("issueCreate", {})

    def update_issue(self, issue_id: str, **kwargs) -> dict:
        """Update an issue.

        Args:
            issue_id: Issue UUID.
            kwargs:   Fields to update (title, description, stateId, priority,
                      assigneeId, projectId, labelIds, etc.).

        Returns:
            Dict with "success" and updated "issue".
        """
        parts = []
        for key, val in kwargs.items():
            if isinstance(val, str):
                parts.append(f'{key}: "{_esc(val)}"')
            elif isinstance(val, bool):
                parts.append(f"{key}: {'true' if val else 'false'}")
            elif isinstance(val, (int, float)):
                parts.append(f"{key}: {val}")
            elif isinstance(val, list):
                items = ", ".join(f'"{v}"' for v in val)
                parts.append(f"{key}: [{items}]")
        input_str = ", ".join(parts)

        query = (
            'mutation { issueUpdate(id: "%s", input: {%s}) { success issue '
            "{ id identifier title state { name } } } }" % (issue_id, input_str)
        )
        return self._query(query).get("issueUpdate", {})

    def delete_issue(self, issue_id: str) -> dict:
        """Delete (archive) an issue.

        Args:
            issue_id: Issue UUID.

        Returns:
            Dict with "success".
        """
        query = 'mutation { issueArchive(id: "%s") { success } }' % issue_id
        return self._query(query).get("issueArchive", {})

    def search_issues(self, query_text: str, first: int = 25) -> list[dict]:
        """Search issues by text.

        Args:
            query_text: Search string.
            first:      Max results.

        Returns:
            List of issue dicts.
        """
        query = """
        query($query: String!, $first: Int!) {
          searchIssues(query: $query, first: $first) {
            nodes { id identifier title state { name } priority
                    assignee { name } createdAt }
          }
        }
        """
        data = self._query(query, {"query": query_text, "first": first})
        return data.get("searchIssues", {}).get("nodes", [])

    # -- Comments ----------------------------------------------------------

    def add_comment(self, issue_id: str, body: str) -> dict:
        """Add a comment to an issue.

        Args:
            issue_id: Issue UUID.
            body:     Markdown comment body.

        Returns:
            Dict with "success" and created "comment".
        """
        query = (
            'mutation { commentCreate(input: {issueId: "%s", body: "%s"}) '
            "{ success comment { id body createdAt } } }"
            % (issue_id, _esc(body))
        )
        return self._query(query).get("commentCreate", {})

    # -- Teams -------------------------------------------------------------

    def list_teams(self) -> list[dict]:
        """List all teams.

        Returns:
            List of team dicts.
        """
        query = """
        { teams { nodes { id name key description } } }
        """
        return self._query(query).get("teams", {}).get("nodes", [])

    # -- Projects ----------------------------------------------------------

    def list_projects(self, first: int = 50) -> list[dict]:
        """List projects.

        Args:
            first: Max results.

        Returns:
            List of project dicts.
        """
        query = """
        query($first: Int!) {
          projects(first: $first) {
            nodes { id name description state startDate targetDate
                    lead { name } teams { nodes { name } } }
          }
        }
        """
        return self._query(query, {"first": first}).get("projects", {}).get("nodes", [])

    # -- Workflow States ----------------------------------------------------

    def list_workflow_states(self, team_id: str) -> list[dict]:
        """List workflow states for a team.

        Args:
            team_id: Team UUID.

        Returns:
            List of state dicts with id, name, type, position.
        """
        query = """
        query($id: String!) {
          team(id: $id) {
            states { nodes { id name type position } }
          }
        }
        """
        data = self._query(query, {"id": team_id})
        return data.get("team", {}).get("states", {}).get("nodes", [])

    # -- internal helpers --------------------------------------------------

    def _query(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query against the Linear API."""
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = self.session.post(_API_URL, json=payload)
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"Linear API error: {body['errors']}")
        return body.get("data", body)


def _esc(s: str) -> str:
    """Escape a string for use inside a GraphQL string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
