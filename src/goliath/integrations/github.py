"""
GitHub Integration — manage repos, issues, pull requests, and files via GitHub API v3.

SETUP INSTRUCTIONS
==================

1. Go to https://github.com/settings/tokens

2. Click "Generate new token" > "Generate new token (classic)".

3. Select scopes:
     - repo        (full repo access)
     - read:org    (read org membership, optional)
     - workflow    (trigger Actions, optional)

4. Generate the token and add it to your .env:
     GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

5. Optionally set a default owner/org:
     GITHUB_OWNER=your-username-or-org

Usage:
    from goliath.integrations.github import GitHubClient

    gh = GitHubClient()

    # --- Repositories ---
    repos = gh.list_repos()
    repo = gh.get_repo("owner/repo")
    gh.create_repo("my-new-project", description="Built by GOLIATH", private=False)

    # --- Issues ---
    issues = gh.list_issues("owner/repo")
    gh.create_issue("owner/repo", title="Bug report", body="Something broke.")
    gh.comment_on_issue("owner/repo", issue_number=1, body="Looking into this.")

    # --- Pull Requests ---
    prs = gh.list_pulls("owner/repo")
    gh.create_pull("owner/repo", title="Add feature", head="feature-branch", base="main")

    # --- Files ---
    content = gh.get_file("owner/repo", "README.md")
    gh.create_or_update_file(
        "owner/repo", "docs/notes.md",
        content="# Notes\\nAutomated by GOLIATH.",
        message="Add notes file",
    )

    # --- Actions ---
    gh.trigger_workflow("owner/repo", "build.yml", ref="main")
"""

import base64

import requests

from goliath import config

_API_BASE = "https://api.github.com"


class GitHubClient:
    """GitHub API v3 client for repos, issues, PRs, files, and Actions."""

    def __init__(self, token: str | None = None):
        self.token = token or config.GITHUB_TOKEN
        if not self.token:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. "
                "Add it to .env or pass token to GitHubClient(). "
                "See integrations/github.py for setup instructions."
            )
        self.owner = config.GITHUB_OWNER
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    # -- Repositories ------------------------------------------------------

    def list_repos(self, owner: str | None = None, per_page: int = 30) -> list[dict]:
        """List repositories for a user or org."""
        target = owner or self.owner
        if target:
            return self._get(f"/users/{target}/repos", params={"per_page": per_page})
        return self._get("/user/repos", params={"per_page": per_page})

    def get_repo(self, repo: str) -> dict:
        """Get repository details. repo format: 'owner/name'."""
        return self._get(f"/repos/{repo}")

    def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = False,
    ) -> dict:
        """Create a new repository for the authenticated user."""
        return self._post(
            "/user/repos",
            json={
                "name": name,
                "description": description,
                "private": private,
            },
        )

    # -- Issues ------------------------------------------------------------

    def list_issues(
        self,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[dict]:
        """List issues for a repository."""
        return self._get(
            f"/repos/{repo}/issues",
            params={
                "state": state,
                "per_page": per_page,
            },
        )

    def create_issue(
        self, repo: str, title: str, body: str = "", labels: list[str] | None = None
    ) -> dict:
        """Create a new issue."""
        payload: dict = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        return self._post(f"/repos/{repo}/issues", json=payload)

    def comment_on_issue(self, repo: str, issue_number: int, body: str) -> dict:
        """Add a comment to an issue or pull request."""
        return self._post(
            f"/repos/{repo}/issues/{issue_number}/comments", json={"body": body}
        )

    # -- Pull Requests -----------------------------------------------------

    def list_pulls(
        self,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[dict]:
        """List pull requests for a repository."""
        return self._get(
            f"/repos/{repo}/pulls",
            params={
                "state": state,
                "per_page": per_page,
            },
        )

    def create_pull(
        self,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> dict:
        """Create a pull request."""
        return self._post(
            f"/repos/{repo}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
            },
        )

    # -- Files -------------------------------------------------------------

    def get_file(self, repo: str, path: str, ref: str | None = None) -> dict:
        """Get a file's content and metadata from a repository.

        Returns a dict with 'content' (decoded), 'sha', 'path', etc.
        """
        params = {}
        if ref:
            params["ref"] = ref
        data = self._get(f"/repos/{repo}/contents/{path}", params=params)
        if data.get("content"):
            data["decoded_content"] = base64.b64decode(data["content"]).decode("utf-8")
        return data

    def create_or_update_file(
        self,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
    ) -> dict:
        """Create or update a file in a repository.

        If the file already exists, its SHA is fetched automatically.
        """
        payload: dict = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        }
        if branch:
            payload["branch"] = branch

        # Check if file exists to get its SHA for updates
        try:
            existing = self.get_file(repo, path, ref=branch)
            payload["sha"] = existing["sha"]
        except requests.HTTPError:
            pass  # File doesn't exist yet — create it

        return self._put(f"/repos/{repo}/contents/{path}", json=payload)

    # -- Actions -----------------------------------------------------------

    def trigger_workflow(
        self,
        repo: str,
        workflow: str,
        ref: str = "main",
        inputs: dict | None = None,
    ) -> None:
        """Trigger a GitHub Actions workflow dispatch.

        Args:
            repo:     'owner/name'
            workflow: Workflow filename (e.g. 'build.yml') or ID.
            ref:      Branch or tag to run on.
            inputs:   Optional workflow input parameters.
        """
        payload: dict = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs
        self._post(
            f"/repos/{repo}/actions/workflows/{workflow}/dispatches",
            json=payload,
        )

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()

    def _put(self, path: str, **kwargs) -> dict:
        resp = self.session.put(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
