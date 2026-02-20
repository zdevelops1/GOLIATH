"""
Figma Integration — read files, components, comments, and export images via the Figma REST API.

SETUP INSTRUCTIONS
==================

1. Log in to Figma at https://www.figma.com/

2. Go to Settings > Account > Personal access tokens
   (https://www.figma.com/developers/api#access-tokens).

3. Click "Generate new token", give it a description (e.g. "GOLIATH").

4. Copy the token and add it to your .env:
     FIGMA_ACCESS_TOKEN=figd_xxxxxxxxxxxxxxxx

IMPORTANT NOTES
===============
- Authentication uses a Personal Access Token (Bearer or X-Figma-Token header).
- API docs: https://www.figma.com/developers/api
- Rate limit: 30 requests per minute per token.
- File keys are found in the Figma URL: figma.com/file/<FILE_KEY>/...
- Node IDs use the format "X:Y" (e.g. "1:2").

Usage:
    from goliath.integrations.figma import FigmaClient

    fig = FigmaClient()

    # Get a file
    file = fig.get_file("FILE_KEY")

    # Get specific nodes from a file
    nodes = fig.get_file_nodes("FILE_KEY", node_ids=["1:2", "3:4"])

    # List comments on a file
    comments = fig.get_comments("FILE_KEY")

    # Post a comment
    fig.post_comment("FILE_KEY", message="Looks good!", x=100, y=200)

    # Export nodes as PNG
    images = fig.export_images("FILE_KEY", node_ids=["1:2"], format="png", scale=2)

    # Get file components (design system)
    components = fig.get_components("FILE_KEY")

    # Get team projects
    projects = fig.get_team_projects("TEAM_ID")

    # Get project files
    files = fig.get_project_files("PROJECT_ID")
"""

import requests

from goliath import config

_API_BASE = "https://api.figma.com/v1"


class FigmaClient:
    """Figma REST API client for files, components, comments, and exports."""

    def __init__(self):
        if not config.FIGMA_ACCESS_TOKEN:
            raise RuntimeError(
                "FIGMA_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/figma.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "X-Figma-Token": config.FIGMA_ACCESS_TOKEN,
        })

    # -- Files -------------------------------------------------------------

    def get_file(self, file_key: str, **kwargs) -> dict:
        """Get a Figma file.

        Args:
            file_key: File key from the Figma URL.
            kwargs:   Optional params (depth, geometry, plugin_data).

        Returns:
            File dict with document tree, components, styles, etc.
        """
        return self._get(f"/files/{file_key}", params=kwargs)

    def get_file_nodes(
        self, file_key: str, node_ids: list[str], **kwargs
    ) -> dict:
        """Get specific nodes from a file.

        Args:
            file_key: File key.
            node_ids: List of node IDs (e.g. ["1:2", "3:4"]).
            kwargs:   Optional params (depth, geometry, plugin_data).

        Returns:
            Dict mapping node IDs to their subtrees.
        """
        params = {"ids": ",".join(node_ids), **kwargs}
        return self._get(f"/files/{file_key}/nodes", params=params)

    # -- Comments ----------------------------------------------------------

    def get_comments(self, file_key: str) -> list[dict]:
        """Get all comments on a file.

        Args:
            file_key: File key.

        Returns:
            List of comment dicts.
        """
        return self._get(f"/files/{file_key}/comments").get("comments", [])

    def post_comment(
        self,
        file_key: str,
        message: str,
        x: float = 0,
        y: float = 0,
        node_id: str | None = None,
    ) -> dict:
        """Post a comment on a file.

        Args:
            file_key: File key.
            message:  Comment text.
            x:        X coordinate for the comment pin.
            y:        Y coordinate for the comment pin.
            node_id:  Optional node to attach the comment to.

        Returns:
            Created comment dict.
        """
        data: dict = {
            "message": message,
            "client_meta": {"x": x, "y": y},
        }
        if node_id:
            data["client_meta"]["node_id"] = node_id
            data["client_meta"]["node_offset"] = {"x": x, "y": y}
        return self._post(f"/files/{file_key}/comments", json=data)

    def delete_comment(self, file_key: str, comment_id: str) -> None:
        """Delete a comment.

        Args:
            file_key:   File key.
            comment_id: Comment ID.
        """
        resp = self.session.delete(
            f"{_API_BASE}/files/{file_key}/comments/{comment_id}"
        )
        resp.raise_for_status()

    # -- Exports -----------------------------------------------------------

    def export_images(
        self,
        file_key: str,
        node_ids: list[str],
        format: str = "png",
        scale: float = 1,
        **kwargs,
    ) -> dict:
        """Export nodes as images.

        Args:
            file_key: File key.
            node_ids: Node IDs to export.
            format:   "jpg", "png", "svg", or "pdf".
            scale:    Image scale (0.01–4).
            kwargs:   Additional params (svg_include_id, svg_simplify_stroke, etc.).

        Returns:
            Dict mapping node IDs to image download URLs.
        """
        params = {
            "ids": ",".join(node_ids),
            "format": format,
            "scale": scale,
            **kwargs,
        }
        return self._get(f"/images/{file_key}", params=params).get("images", {})

    # -- Components & Styles -----------------------------------------------

    def get_components(self, file_key: str) -> list[dict]:
        """Get components from a file.

        Args:
            file_key: File key.

        Returns:
            List of component dicts.
        """
        data = self._get(f"/files/{file_key}/components")
        return data.get("meta", {}).get("components", [])

    def get_styles(self, file_key: str) -> list[dict]:
        """Get styles from a file.

        Args:
            file_key: File key.

        Returns:
            List of style dicts.
        """
        data = self._get(f"/files/{file_key}/styles")
        return data.get("meta", {}).get("styles", [])

    # -- Teams & Projects --------------------------------------------------

    def get_team_projects(self, team_id: str) -> list[dict]:
        """Get projects for a team.

        Args:
            team_id: Team ID.

        Returns:
            List of project dicts.
        """
        return self._get(f"/teams/{team_id}/projects").get("projects", [])

    def get_project_files(self, project_id: str) -> list[dict]:
        """Get files in a project.

        Args:
            project_id: Project ID.

        Returns:
            List of file dicts.
        """
        return self._get(f"/projects/{project_id}/files").get("files", [])

    # -- Version History ---------------------------------------------------

    def get_file_versions(self, file_key: str) -> list[dict]:
        """Get version history for a file.

        Args:
            file_key: File key.

        Returns:
            List of version dicts.
        """
        return self._get(f"/files/{file_key}/versions").get("versions", [])

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
