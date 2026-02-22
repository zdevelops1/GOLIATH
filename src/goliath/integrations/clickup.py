"""
ClickUp Integration — manage tasks, lists, and spaces via the ClickUp REST API.

SETUP INSTRUCTIONS
==================

1. Log in to ClickUp at https://app.clickup.com/

2. Go to Settings > Apps (or navigate to https://app.clickup.com/settings/apps).

3. Under "API Token", click "Generate" to create a personal API token.
   (Or create an OAuth2 app for team-wide access.)

4. Copy the token and add it to your .env:
     CLICKUP_API_TOKEN=pk_xxxxxxxx

IMPORTANT NOTES
===============
- API docs: https://clickup.com/api/
- Rate limit: 100 requests per minute per token.
- Authentication: Bearer token.
- Base URL: https://api.clickup.com/api/v2

Usage:
    from goliath.integrations.clickup import ClickUpClient

    cu = ClickUpClient()

    # List workspaces (teams)
    teams = cu.list_teams()

    # List spaces in a workspace
    spaces = cu.list_spaces("team-id")

    # List folders in a space
    folders = cu.list_folders("space-id")

    # List lists in a folder
    lists = cu.list_lists("folder-id")

    # Get tasks from a list
    tasks = cu.list_tasks("list-id")

    # Create a task
    task = cu.create_task("list-id", name="Fix login bug", description="Details here")

    # Update a task
    cu.update_task("task-id", status="in progress")

    # Get task details
    task = cu.get_task("task-id")

    # Add a comment to a task
    cu.add_comment("task-id", comment_text="Investigating now.")

    # Delete a task
    cu.delete_task("task-id")
"""

import requests

from goliath import config

_API_BASE = "https://api.clickup.com/api/v2"


class ClickUpClient:
    """ClickUp REST API client for tasks, lists, spaces, and teams."""

    def __init__(self):
        if not config.CLICKUP_API_TOKEN:
            raise RuntimeError(
                "CLICKUP_API_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/clickup.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": config.CLICKUP_API_TOKEN,
            "Content-Type": "application/json",
        })

    # -- Teams (Workspaces) ----------------------------------------------------

    def list_teams(self) -> list[dict]:
        """List workspaces (teams) the token has access to.

        Returns:
            List of team dicts.
        """
        data = self._get("/team")
        return data.get("teams", [])

    # -- Spaces ----------------------------------------------------------------

    def list_spaces(self, team_id: str, archived: bool = False) -> list[dict]:
        """List spaces in a workspace.

        Args:
            team_id:  Team (workspace) ID.
            archived: Include archived spaces.

        Returns:
            List of space dicts.
        """
        data = self._get(
            f"/team/{team_id}/space",
            params={"archived": str(archived).lower()},
        )
        return data.get("spaces", [])

    def get_space(self, space_id: str) -> dict:
        """Get space details.

        Args:
            space_id: Space ID.

        Returns:
            Space dict.
        """
        return self._get(f"/space/{space_id}")

    # -- Folders ---------------------------------------------------------------

    def list_folders(self, space_id: str, archived: bool = False) -> list[dict]:
        """List folders in a space.

        Args:
            space_id: Space ID.
            archived: Include archived folders.

        Returns:
            List of folder dicts.
        """
        data = self._get(
            f"/space/{space_id}/folder",
            params={"archived": str(archived).lower()},
        )
        return data.get("folders", [])

    def get_folder(self, folder_id: str) -> dict:
        """Get folder details.

        Args:
            folder_id: Folder ID.

        Returns:
            Folder dict.
        """
        return self._get(f"/folder/{folder_id}")

    # -- Lists -----------------------------------------------------------------

    def list_lists(self, folder_id: str, archived: bool = False) -> list[dict]:
        """List lists in a folder.

        Args:
            folder_id: Folder ID.
            archived:  Include archived lists.

        Returns:
            List of list dicts.
        """
        data = self._get(
            f"/folder/{folder_id}/list",
            params={"archived": str(archived).lower()},
        )
        return data.get("lists", [])

    def get_list(self, list_id: str) -> dict:
        """Get list details.

        Args:
            list_id: List ID.

        Returns:
            List dict.
        """
        return self._get(f"/list/{list_id}")

    # -- Tasks -----------------------------------------------------------------

    def list_tasks(
        self,
        list_id: str,
        archived: bool = False,
        page: int = 0,
        statuses: list[str] | None = None,
    ) -> list[dict]:
        """List tasks in a list.

        Args:
            list_id:  List ID.
            archived: Include archived/closed tasks.
            page:     Page number (0-indexed).
            statuses: Filter by status names.

        Returns:
            List of task dicts.
        """
        params: dict = {
            "archived": str(archived).lower(),
            "page": page,
        }
        if statuses:
            params["statuses[]"] = statuses
        data = self._get(f"/list/{list_id}/task", params=params)
        return data.get("tasks", [])

    def get_task(self, task_id: str) -> dict:
        """Get task details.

        Args:
            task_id: Task ID.

        Returns:
            Task dict.
        """
        return self._get(f"/task/{task_id}")

    def create_task(
        self,
        list_id: str,
        name: str,
        description: str = "",
        status: str | None = None,
        priority: int | None = None,
        assignees: list[int] | None = None,
        due_date: int | None = None,
        **kwargs,
    ) -> dict:
        """Create a task.

        Args:
            name:        Task name.
            list_id:     List ID.
            description: Task description (supports markdown).
            status:      Status name.
            priority:    Priority (1=urgent, 2=high, 3=normal, 4=low).
            assignees:   List of user IDs.
            due_date:    Due date as Unix timestamp (ms).
            kwargs:      Additional fields (tags, time_estimate, etc.).

        Returns:
            Created task dict.
        """
        payload: dict = {"name": name, "description": description, **kwargs}
        if status:
            payload["status"] = status
        if priority is not None:
            payload["priority"] = priority
        if assignees:
            payload["assignees"] = assignees
        if due_date is not None:
            payload["due_date"] = due_date
        return self._post(f"/list/{list_id}/task", json=payload)

    def update_task(self, task_id: str, **kwargs) -> dict:
        """Update a task.

        Args:
            task_id: Task ID.
            kwargs:  Fields to update (name, description, status, priority, etc.).

        Returns:
            Updated task dict.
        """
        resp = self.session.put(f"{_API_BASE}/task/{task_id}", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    def delete_task(self, task_id: str) -> dict:
        """Delete a task.

        Args:
            task_id: Task ID.

        Returns:
            Deletion result.
        """
        resp = self.session.delete(f"{_API_BASE}/task/{task_id}")
        resp.raise_for_status()
        return {"status": "deleted"}

    # -- Comments --------------------------------------------------------------

    def add_comment(self, task_id: str, comment_text: str) -> dict:
        """Add a comment to a task.

        Args:
            task_id:      Task ID.
            comment_text: Comment body.

        Returns:
            Comment result.
        """
        return self._post(
            f"/task/{task_id}/comment", json={"comment_text": comment_text}
        )

    def list_comments(self, task_id: str) -> list[dict]:
        """List comments on a task.

        Args:
            task_id: Task ID.

        Returns:
            List of comment dicts.
        """
        data = self._get(f"/task/{task_id}/comment")
        return data.get("comments", [])

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
