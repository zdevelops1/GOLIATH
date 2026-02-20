"""
Canva Integration — manage designs, folders, and exports via the Canva Connect API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.canva.com/developers/ and log in.

2. Create an integration (app) from the Developer Portal.

3. Under "Authorization", configure the OAuth2 flow to obtain an access
   token, or generate a token directly from the portal for testing.

4. Add to your .env:
     CANVA_ACCESS_TOKEN=your_oauth_access_token

IMPORTANT NOTES
===============
- Authentication uses OAuth2 Bearer tokens.
- API docs: https://www.canva.dev/docs/connect/
- Rate limit: varies by endpoint (typically 100 requests/minute).
- The Connect API supports design management, asset uploads, and exports.
- Design creation via API uses templates or brand templates.

Usage:
    from goliath.integrations.canva import CanvaClient

    canva = CanvaClient()

    # List designs
    designs = canva.list_designs()

    # Get a design
    design = canva.get_design("DESIGN_ID")

    # Create a design from scratch
    design = canva.create_design(
        title="Social Media Post",
        design_type="InstagramPost",
    )

    # Export a design as PNG
    export = canva.export_design("DESIGN_ID", format="png")

    # List folders
    folders = canva.list_folders()

    # Upload an asset (image)
    asset = canva.upload_asset(name="Logo", url="https://example.com/logo.png")

    # List brand templates
    templates = canva.list_brand_templates()
"""

import requests

from goliath import config

_API_BASE = "https://api.canva.com/rest/v1"


class CanvaClient:
    """Canva Connect API client for designs, folders, and exports."""

    def __init__(self):
        if not config.CANVA_ACCESS_TOKEN:
            raise RuntimeError(
                "CANVA_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/canva.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.CANVA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        })

    # -- Designs -----------------------------------------------------------

    def list_designs(self, query: str | None = None, limit: int = 25) -> list[dict]:
        """List the user's designs.

        Args:
            query: Optional search query.
            limit: Max results.

        Returns:
            List of design dicts.
        """
        params: dict = {"limit": limit}
        if query:
            params["query"] = query
        return self._get("/designs", params=params).get("items", [])

    def get_design(self, design_id: str) -> dict:
        """Get a design by ID.

        Args:
            design_id: Design ID.

        Returns:
            Design dict with title, urls, thumbnail, etc.
        """
        return self._get(f"/designs/{design_id}").get("design", {})

    def create_design(
        self,
        title: str = "",
        design_type: str | None = None,
        width: int | None = None,
        height: int | None = None,
        **kwargs,
    ) -> dict:
        """Create a new design.

        Args:
            title:       Design title.
            design_type: Preset type (e.g. "InstagramPost", "Presentation").
            width:       Custom width in pixels (if no design_type).
            height:      Custom height in pixels (if no design_type).
            kwargs:      Additional fields (asset_id for templates, etc.).

        Returns:
            Created design dict.
        """
        data: dict = {**kwargs}
        if title:
            data["title"] = title
        if design_type:
            data["design_type"] = {"type": design_type}
        elif width and height:
            data["design_type"] = {
                "type": "custom",
                "width": width,
                "height": height,
            }
        return self._post("/designs", json=data).get("design", {})

    def delete_design(self, design_id: str) -> None:
        """Delete a design.

        Args:
            design_id: Design ID.
        """
        resp = self.session.delete(f"{_API_BASE}/designs/{design_id}")
        resp.raise_for_status()

    # -- Exports -----------------------------------------------------------

    def export_design(
        self,
        design_id: str,
        format: str = "png",
        quality: str = "regular",
        pages: list[int] | None = None,
    ) -> dict:
        """Start an export job for a design.

        Args:
            design_id: Design ID.
            format:    "png", "jpg", "pdf", "gif", "pptx", or "mp4".
            quality:   "regular" or "high".
            pages:     List of page indices to export (None = all).

        Returns:
            Export job dict with id and status.
        """
        data: dict = {
            "design_id": design_id,
            "format": {"type": format},
            "quality": quality,
        }
        if pages is not None:
            data["pages"] = pages
        return self._post("/exports", json=data).get("job", {})

    def get_export(self, export_id: str) -> dict:
        """Check the status of an export job.

        Args:
            export_id: Export job ID.

        Returns:
            Export job dict with status and download URLs when complete.
        """
        return self._get(f"/exports/{export_id}").get("job", {})

    # -- Folders -----------------------------------------------------------

    def list_folders(self, limit: int = 25) -> list[dict]:
        """List folders.

        Args:
            limit: Max results.

        Returns:
            List of folder dicts.
        """
        return self._get("/folders", params={"limit": limit}).get("items", [])

    def create_folder(self, name: str, parent_folder_id: str | None = None) -> dict:
        """Create a folder.

        Args:
            name:             Folder name.
            parent_folder_id: Parent folder ID (None = root).

        Returns:
            Created folder dict.
        """
        data: dict = {"name": name}
        if parent_folder_id:
            data["parent_folder_id"] = parent_folder_id
        return self._post("/folders", json=data).get("folder", {})

    # -- Assets ------------------------------------------------------------

    def upload_asset(self, name: str, url: str) -> dict:
        """Upload an asset from a URL.

        Args:
            name: Asset name.
            url:  Public URL of the image/video to upload.

        Returns:
            Asset upload job dict.
        """
        data = {
            "name": name,
            "url": url,
        }
        return self._post("/asset-uploads", json=data).get("job", {})

    def get_asset_upload(self, job_id: str) -> dict:
        """Check the status of an asset upload.

        Args:
            job_id: Upload job ID.

        Returns:
            Job dict with status and asset info.
        """
        return self._get(f"/asset-uploads/{job_id}").get("job", {})

    # -- Brand Templates ---------------------------------------------------

    def list_brand_templates(self, limit: int = 25) -> list[dict]:
        """List brand templates.

        Args:
            limit: Max results.

        Returns:
            List of brand template dicts.
        """
        return self._get("/brand-templates", params={"limit": limit}).get("items", [])

    def get_brand_template(self, template_id: str) -> dict:
        """Get a brand template.

        Args:
            template_id: Brand template ID.

        Returns:
            Brand template dict.
        """
        return self._get(f"/brand-templates/{template_id}").get("brand_template", {})

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
