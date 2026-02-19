"""
LinkedIn Integration — share posts, articles, and manage profile via LinkedIn API v2.

SETUP INSTRUCTIONS
==================

1. Go to https://developer.linkedin.com/ and create an app.

2. Under the "Auth" tab, note your Client ID and Client Secret.

3. Request the following OAuth 2.0 scopes (Products tab):
   - Share on LinkedIn: w_member_social
   - Sign In with LinkedIn: openid, profile, email
   - For organization posts: w_organization_social, r_organization_social

4. Generate an access token via the OAuth 2.0 3-legged flow,
   or use the token from the LinkedIn Developer Portal's OAuth tools.

5. Get your LinkedIn member URN:
   GET https://api.linkedin.com/v2/userinfo
   Your sub (person ID) is returned.

6. Add to your .env:
     LINKEDIN_ACCESS_TOKEN=your-access-token
     LINKEDIN_PERSON_ID=your-person-id

IMPORTANT NOTES
===============
- Access tokens expire after 60 days. Refresh tokens last 365 days.
- Rate limits vary per endpoint; posting is limited to ~100/day.
- Image/video uploads require a two-step process: register upload, then upload bytes.
- Organization posts require additional product approval from LinkedIn.

Usage:
    from goliath.integrations.linkedin import LinkedInClient

    li = LinkedInClient()

    # Share a text post
    li.create_post("Hello from GOLIATH!")

    # Share a post with a link
    li.create_post("Check this out", link_url="https://example.com")

    # Share a post with an image
    li.create_image_post("Look at this!", "photo.jpg")

    # Get your profile
    profile = li.get_profile()
"""

from pathlib import Path

import requests

from goliath import config

_API_BASE = "https://api.linkedin.com"


class LinkedInClient:
    """LinkedIn API v2 client for sharing posts and managing profile."""

    def __init__(self):
        if not config.LINKEDIN_ACCESS_TOKEN:
            raise RuntimeError(
                "LINKEDIN_ACCESS_TOKEN is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/linkedin.py for setup instructions."
            )
        if not config.LINKEDIN_PERSON_ID:
            raise RuntimeError(
                "LINKEDIN_PERSON_ID is not set. "
                "Add it to .env or export as an environment variable."
            )

        self._person_id = config.LINKEDIN_PERSON_ID
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202402",
            }
        )

    # -- public API --------------------------------------------------------

    def get_profile(self) -> dict:
        """Get the authenticated user's profile info.

        Returns:
            Profile data dict (name, email, picture).
        """
        resp = self.session.get(f"{_API_BASE}/v2/userinfo")
        resp.raise_for_status()
        return resp.json()

    def create_post(
        self,
        text: str,
        link_url: str | None = None,
        visibility: str = "PUBLIC",
    ) -> dict:
        """Create a text or link post on LinkedIn.

        Args:
            text:       Post body text.
            link_url:   Optional URL to attach as a link preview.
            visibility: "PUBLIC", "CONNECTIONS", or "LOGGED_IN".

        Returns:
            API response dict with the post URN.
        """
        author = f"urn:li:person:{self._person_id}"
        body: dict = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
        }

        if link_url:
            share = body["specificContent"]["com.linkedin.ugc.ShareContent"]
            share["shareMediaCategory"] = "ARTICLE"
            share["media"] = [
                {
                    "status": "READY",
                    "originalUrl": link_url,
                }
            ]

        resp = self.session.post(f"{_API_BASE}/v2/ugcPosts", json=body)
        resp.raise_for_status()
        return resp.json()

    def create_image_post(
        self,
        text: str,
        image_path: str,
        visibility: str = "PUBLIC",
    ) -> dict:
        """Create a post with an image.

        Args:
            text:       Post body text.
            image_path: Path to the image file.
            visibility: "PUBLIC", "CONNECTIONS", or "LOGGED_IN".

        Returns:
            API response dict with the post URN.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Step 1: Register the upload
        owner = f"urn:li:person:{self._person_id}"
        register_body = {
            "registerUploadRequest": {
                "owner": owner,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [
                    {
                        "identifier": "urn:li:userGeneratedContent",
                        "relationshipType": "OWNER",
                    }
                ],
            }
        }
        reg_resp = self.session.post(
            f"{_API_BASE}/v2/assets?action=registerUpload",
            json=register_body,
        )
        reg_resp.raise_for_status()
        reg_data = reg_resp.json()

        upload_url = reg_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = reg_data["value"]["asset"]

        # Step 2: Upload the image bytes
        with open(path, "rb") as f:
            up_resp = self.session.put(
                upload_url,
                data=f,
                headers={"Content-Type": "application/octet-stream"},
            )
        up_resp.raise_for_status()

        # Step 3: Create the post with the uploaded asset
        body = {
            "author": owner,
            "lifecycleState": "PUBLISHED",
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": asset,
                        }
                    ],
                }
            },
        }
        resp = self.session.post(f"{_API_BASE}/v2/ugcPosts", json=body)
        resp.raise_for_status()
        return resp.json()

    def delete_post(self, post_urn: str) -> None:
        """Delete a post.

        Args:
            post_urn: The URN of the post (e.g. "urn:li:share:1234567890").
        """
        encoded = post_urn.replace(":", "%3A")
        resp = self.session.delete(f"{_API_BASE}/v2/ugcPosts/{encoded}")
        resp.raise_for_status()

    def get_post_stats(self, post_urn: str) -> dict:
        """Get engagement statistics for a post.

        Args:
            post_urn: The URN of the post.

        Returns:
            Dict with like count, comment count, share count, etc.
        """
        encoded = post_urn.replace(":", "%3A")
        resp = self.session.get(
            f"{_API_BASE}/v2/socialActions/{encoded}",
        )
        resp.raise_for_status()
        return resp.json()
