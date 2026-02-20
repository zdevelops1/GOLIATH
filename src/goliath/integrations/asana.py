"""
Asana Integration — manage projects, tasks, and workspaces via the Asana REST API.

SETUP INSTRUCTIONS
==================

1. Log in to Asana at https://app.asana.com/

2. Go to https://app.asana.com/0/developer-console and click "Create new token".

3. Give it a description (e.g. "GOLIATH") and click "Create token".

4. Copy the token and add it to your .env:
     ASANA_ACCESS_TOKEN=1/12345678901234:abcdef...

IMPORTANT NOTES
===============
- Authentication uses a Personal Access Token (Bearer token).
- API docs: https://developers.asana.com/reference/rest-api-reference
- Rate limit: 1500 requests per minute.
- All tasks belong to a project, which belongs to a workspace.

Usage:
    from goliath.integrations.asana import AsanaClient

    asana = AsanaClient()

    # List workspaces
    workspaces = asana.list_workspaces()

    # List projects in a workspace
    projects = asana.list_projects(workspace_gid="12345")

    # Create a task
    task = asana.create_task(
        project_gid="67890",
        name="Build landing page",
        notes="Design and implement the new landing page.",
    )

    # Get a task
    task = asana.get_task("111222333")

    # Update a task
    asana.update_task("111222333", completed=True)

    # Add a comment to a task
    asana.add_comment("111222333", text="Done! Ready for review.")

    # Search tasks
    results = asana.search_tasks(workspace_gid="12345", text="landing page")
"""

import requests

from goliath import config

_API_BASE = "https://app.asana.com/api/1.0"


class AsanaClient:
    """Asana REST API client for projects, tasks, and workspaces."""

    def __init__(self):
        if not config.ASANA_ACCESS_TOKEN:
            raise RuntimeError(
                "ASANA_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/asana.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.ASANA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        })

    # -- Workspaces --------------------------------------------------------

    def list_workspaces(self) -> list[dict]:
        """List all workspaces the user has access to.

        Returns:
            List of workspace dicts with gid and name.
        """
        return self._get("/workspaces")

    # -- Projects ----------------------------------------------------------

    def list_projects(self, workspace_gid: str) -> list[dict]:
        """List projects in a workspace.

        Args:
            workspace_gid: Workspace GID.

        Returns:
            List of project dicts.
        """
        return self._get("/projects", params={"workspace": workspace_gid})

    def create_project(
        self,
        workspace_gid: str,
        name: str,
        notes: str = "",
        **kwargs,
    ) -> dict:
        """Create a new project.

        Args:
            workspace_gid: Workspace GID.
            name:          Project name.
            notes:         Project description.
            kwargs:        Additional fields (color, due_on, etc.).

        Returns:
            Created project dict.
        """
        data = {"workspace": workspace_gid, "name": name, "notes": notes, **kwargs}
        return self._post("/projects", json={"data": data})

    # -- Tasks -------------------------------------------------------------

    def create_task(
        self,
        project_gid: str,
        name: str,
        notes: str = "",
        assignee: str | None = None,
        due_on: str | None = None,
        **kwargs,
    ) -> dict:
        """Create a new task in a project.

        Args:
            project_gid: Project GID to add the task to.
            name:        Task name.
            notes:       Task description.
            assignee:    Assignee GID or "me".
            due_on:      Due date in YYYY-MM-DD format.
            kwargs:      Additional fields (tags, followers, etc.).

        Returns:
            Created task dict.
        """
        data: dict = {"projects": [project_gid], "name": name, "notes": notes, **kwargs}
        if assignee:
            data["assignee"] = assignee
        if due_on:
            data["due_on"] = due_on
        return self._post("/tasks", json={"data": data})

    def get_task(self, task_gid: str) -> dict:
        """Get a task by GID.

        Args:
            task_gid: Task GID.

        Returns:
            Task dict.
        """
        return self._get(f"/tasks/{task_gid}")

    def update_task(self, task_gid: str, **kwargs) -> dict:
        """Update a task's fields.

        Args:
            task_gid: Task GID.
            kwargs:   Fields to update (name, notes, completed, due_on, etc.).

        Returns:
            Updated task dict.
        """
        return self._put(f"/tasks/{task_gid}", json={"data": kwargs})

    def delete_task(self, task_gid: str) -> None:
        """Delete a task.

        Args:
            task_gid: Task GID.
        """
        resp = self.session.delete(f"{_API_BASE}/tasks/{task_gid}")
        resp.raise_for_status()

    def list_tasks(self, project_gid: str) -> list[dict]:
        """List tasks in a project.

        Args:
            project_gid: Project GID.

        Returns:
            List of task dicts.
        """
        return self._get("/tasks", params={"project": project_gid})

    def search_tasks(
        self, workspace_gid: str, text: str, limit: int = 20
    ) -> list[dict]:
        """Search tasks in a workspace.

        Args:
            workspace_gid: Workspace GID.
            text:          Search query.
            limit:         Max results (1–100).

        Returns:
            List of matching task dicts.
        """
        return self._get(
            f"/workspaces/{workspace_gid}/tasks/search",
            params={"text": text, "limit": limit},
        )

    # -- Comments (Stories) ------------------------------------------------

    def add_comment(self, task_gid: str, text: str) -> dict:
        """Add a comment to a task.

        Args:
            task_gid: Task GID.
            text:     Comment text.

        Returns:
            Created story dict.
        """
        return self._post(
            f"/tasks/{task_gid}/stories", json={"data": {"text": text}}
        )

    def get_comments(self, task_gid: str) -> list[dict]:
        """Get comments on a task.

        Args:
            task_gid: Task GID.

        Returns:
            List of story dicts (filtered to comments).
        """
        stories = self._get(f"/tasks/{task_gid}/stories")
        return [s for s in stories if s.get("type") == "comment"]

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> list[dict] | dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body)

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body)

    def _put(self, path: str, **kwargs) -> dict:
        resp = self.session.put(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body)
