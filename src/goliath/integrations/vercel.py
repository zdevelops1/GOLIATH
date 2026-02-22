"""
Vercel Integration — manage deployments, projects, and domains via the Vercel REST API.

SETUP INSTRUCTIONS
==================

1. Log in to Vercel at https://vercel.com/

2. Go to Settings > Tokens (https://vercel.com/account/tokens).

3. Click "Create" to generate a new token.

4. Copy the token and add it to your .env:
     VERCEL_ACCESS_TOKEN=your-token-here

5. Optionally set your team ID:
     VERCEL_TEAM_ID=team_xxxxxxxx

IMPORTANT NOTES
===============
- API docs: https://vercel.com/docs/rest-api
- Rate limit: 500 requests per minute.
- Authentication: Bearer token.
- All endpoints: https://api.vercel.com

Usage:
    from goliath.integrations.vercel import VercelClient

    vc = VercelClient()

    # List projects
    projects = vc.list_projects()

    # Get project details
    project = vc.get_project("my-project")

    # List deployments
    deploys = vc.list_deployments()

    # Get deployment details
    deploy = vc.get_deployment("dpl_xxxxxxxx")

    # Create a new deployment (from Git)
    deploy = vc.create_deployment(
        name="my-project",
        git_source={"type": "github", "repo": "user/repo", "ref": "main"},
    )

    # List domains for a project
    domains = vc.list_domains("my-project")

    # Add a domain to a project
    vc.add_domain("my-project", domain="app.example.com")

    # Delete a deployment
    vc.delete_deployment("dpl_xxxxxxxx")

    # List environment variables
    env_vars = vc.list_env_vars("my-project")
"""

import requests

from goliath import config

_API_BASE = "https://api.vercel.com"


class VercelClient:
    """Vercel REST API client for deployments, projects, and domains."""

    def __init__(self):
        if not config.VERCEL_ACCESS_TOKEN:
            raise RuntimeError(
                "VERCEL_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/vercel.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.VERCEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        })

        self._team_id = getattr(config, "VERCEL_TEAM_ID", "") or ""

    # -- Projects --------------------------------------------------------------

    def list_projects(self, limit: int = 20) -> list[dict]:
        """List projects.

        Args:
            limit: Max results per page.

        Returns:
            List of project dicts.
        """
        params: dict = {"limit": limit}
        data = self._get("/v9/projects", params=params)
        return data.get("projects", [])

    def get_project(self, project_id: str) -> dict:
        """Get project details.

        Args:
            project_id: Project ID or name.

        Returns:
            Project dict.
        """
        return self._get(f"/v9/projects/{project_id}")

    # -- Deployments -----------------------------------------------------------

    def list_deployments(
        self,
        project_id: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """List deployments.

        Args:
            project_id: Filter by project ID or name.
            limit:      Max results.

        Returns:
            List of deployment dicts.
        """
        params: dict = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        data = self._get("/v6/deployments", params=params)
        return data.get("deployments", [])

    def get_deployment(self, deployment_id: str) -> dict:
        """Get deployment details.

        Args:
            deployment_id: Deployment ID.

        Returns:
            Deployment dict.
        """
        return self._get(f"/v13/deployments/{deployment_id}")

    def create_deployment(self, name: str, git_source: dict, **kwargs) -> dict:
        """Create a deployment.

        Args:
            name:       Project name.
            git_source: Git source dict (type, repo, ref).
            kwargs:     Additional fields (target, environment variables, etc.).

        Returns:
            Created deployment dict.
        """
        payload: dict = {"name": name, "gitSource": git_source, **kwargs}
        return self._post("/v13/deployments", json=payload)

    def delete_deployment(self, deployment_id: str) -> dict:
        """Delete a deployment.

        Args:
            deployment_id: Deployment ID.

        Returns:
            Deletion result dict.
        """
        resp = self.session.delete(
            f"{_API_BASE}/v13/deployments/{deployment_id}",
            params=self._team_params(),
        )
        resp.raise_for_status()
        return {"status": "deleted"}

    # -- Domains ---------------------------------------------------------------

    def list_domains(self, project_id: str) -> list[dict]:
        """List domains for a project.

        Args:
            project_id: Project ID or name.

        Returns:
            List of domain dicts.
        """
        data = self._get(f"/v9/projects/{project_id}/domains")
        return data.get("domains", [])

    def add_domain(self, project_id: str, domain: str) -> dict:
        """Add a domain to a project.

        Args:
            project_id: Project ID or name.
            domain:     Domain name (e.g. "app.example.com").

        Returns:
            Created domain dict.
        """
        return self._post(
            f"/v9/projects/{project_id}/domains", json={"name": domain}
        )

    def remove_domain(self, project_id: str, domain: str) -> dict:
        """Remove a domain from a project.

        Args:
            project_id: Project ID or name.
            domain:     Domain name.

        Returns:
            Removal result.
        """
        resp = self.session.delete(
            f"{_API_BASE}/v9/projects/{project_id}/domains/{domain}",
            params=self._team_params(),
        )
        resp.raise_for_status()
        return {"status": "removed"}

    # -- Environment Variables -------------------------------------------------

    def list_env_vars(self, project_id: str) -> list[dict]:
        """List environment variables for a project.

        Args:
            project_id: Project ID or name.

        Returns:
            List of env var dicts.
        """
        data = self._get(f"/v9/projects/{project_id}/env")
        return data.get("envs", [])

    def create_env_var(
        self,
        project_id: str,
        key: str,
        value: str,
        target: list[str] | None = None,
        env_type: str = "encrypted",
    ) -> dict:
        """Create an environment variable.

        Args:
            project_id: Project ID or name.
            key:        Variable name.
            value:      Variable value.
            target:     Deployment targets (["production", "preview", "development"]).
            env_type:   Type of variable ("encrypted", "plain", "secret").

        Returns:
            Created env var dict.
        """
        payload: dict = {
            "key": key,
            "value": value,
            "type": env_type,
            "target": target or ["production", "preview", "development"],
        }
        return self._post(f"/v10/projects/{project_id}/env", json=payload)

    # -- internal helpers ------------------------------------------------------

    def _team_params(self) -> dict:
        if self._team_id:
            return {"teamId": self._team_id}
        return {}

    def _get(self, path: str, **kwargs) -> dict:
        params = kwargs.pop("params", {})
        params.update(self._team_params())
        resp = self.session.get(f"{_API_BASE}{path}", params=params, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        params = kwargs.pop("params", {})
        params.update(self._team_params())
        resp = self.session.post(f"{_API_BASE}{path}", params=params, **kwargs)
        resp.raise_for_status()
        return resp.json()
