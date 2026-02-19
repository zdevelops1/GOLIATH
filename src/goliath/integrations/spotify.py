"""
Spotify Integration — search music, manage playlists, and control playback via the Spotify Web API.

SETUP INSTRUCTIONS
==================

1. Go to https://developer.spotify.com/dashboard and create an app.

2. Note your Client ID and Client Secret.

3. For user-level access (playlists, playback), complete the OAuth 2.0
   authorization code flow:
   - Redirect URI: http://localhost:8888/callback (add in dashboard)
   - Scopes: playlist-read-private, playlist-modify-public,
     playlist-modify-private, user-read-playback-state,
     user-modify-playback-state, user-read-currently-playing

4. For search/public data only, use Client Credentials flow
   (no user token needed — set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET).

5. Add to your .env:
     SPOTIFY_CLIENT_ID=your-client-id
     SPOTIFY_CLIENT_SECRET=your-client-secret
     SPOTIFY_ACCESS_TOKEN=your-user-access-token  # optional, for user features

IMPORTANT NOTES
===============
- User access tokens expire after 1 hour. Use refresh tokens for production.
- Client credentials tokens (for search only) are auto-generated if no
  user token is provided.
- Rate limit: Spotify doesn't publish exact limits but will return 429s.
- Playback control requires Spotify Premium and an active device.

Usage:
    from goliath.integrations.spotify import SpotifyClient

    sp = SpotifyClient()

    # Search for tracks
    tracks = sp.search("Bohemian Rhapsody", search_type="track", limit=5)

    # Get a playlist
    playlist = sp.get_playlist("37i9dQZF1DXcBWIGoYBM5M")

    # Add tracks to a playlist
    sp.add_to_playlist("playlist_id", uris=["spotify:track:abc123"])

    # Get currently playing
    current = sp.get_currently_playing()
"""

import requests

from goliath import config

_API_BASE = "https://api.spotify.com/v1"
_TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyClient:
    """Spotify Web API client for music search, playlists, and playback."""

    def __init__(self):
        if not config.SPOTIFY_ACCESS_TOKEN and not (
            config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET
        ):
            raise RuntimeError(
                "Spotify credentials not set. Provide either SPOTIFY_ACCESS_TOKEN "
                "(for user features) or both SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET (for search/public data). "
                "See integrations/spotify.py for setup instructions."
            )

        self.session = requests.Session()

        if config.SPOTIFY_ACCESS_TOKEN:
            self.session.headers["Authorization"] = (
                f"Bearer {config.SPOTIFY_ACCESS_TOKEN}"
            )
        else:
            self._authenticate_client_credentials()

    def _authenticate_client_credentials(self):
        """Get an access token using client credentials flow (no user context)."""
        resp = requests.post(
            _TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(config.SPOTIFY_CLIENT_ID, config.SPOTIFY_CLIENT_SECRET),
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {token}"

    # -- Search ------------------------------------------------------------

    def search(
        self,
        query: str,
        search_type: str = "track",
        limit: int = 20,
        market: str | None = None,
    ) -> dict:
        """Search for tracks, albums, artists, or playlists.

        Args:
            query:       Search query string.
            search_type: Comma-separated types — "track", "album", "artist", "playlist".
            limit:       Number of results (1–50).
            market:      ISO 3166-1 alpha-2 country code.

        Returns:
            Search results dict keyed by type (e.g. "tracks", "albums").
        """
        params: dict = {"q": query, "type": search_type, "limit": limit}
        if market:
            params["market"] = market
        return self._get("/search", params=params)

    # -- Tracks ------------------------------------------------------------

    def get_track(self, track_id: str) -> dict:
        """Get a track by ID.

        Args:
            track_id: Spotify track ID.

        Returns:
            Track resource dict.
        """
        return self._get(f"/tracks/{track_id}")

    def get_tracks(self, track_ids: list[str]) -> list[dict]:
        """Get multiple tracks by IDs.

        Args:
            track_ids: List of Spotify track IDs (max 50).

        Returns:
            List of track resource dicts.
        """
        return self._get("/tracks", params={"ids": ",".join(track_ids)}).get(
            "tracks", []
        )

    # -- Albums ------------------------------------------------------------

    def get_album(self, album_id: str) -> dict:
        """Get an album by ID.

        Args:
            album_id: Spotify album ID.

        Returns:
            Album resource dict.
        """
        return self._get(f"/albums/{album_id}")

    # -- Artists -----------------------------------------------------------

    def get_artist(self, artist_id: str) -> dict:
        """Get an artist by ID.

        Args:
            artist_id: Spotify artist ID.

        Returns:
            Artist resource dict.
        """
        return self._get(f"/artists/{artist_id}")

    def get_artist_top_tracks(self, artist_id: str, market: str = "US") -> list[dict]:
        """Get an artist's top tracks.

        Args:
            artist_id: Spotify artist ID.
            market:    ISO country code.

        Returns:
            List of track resource dicts.
        """
        return self._get(
            f"/artists/{artist_id}/top-tracks", params={"market": market}
        ).get("tracks", [])

    # -- Playlists ---------------------------------------------------------

    def get_playlist(self, playlist_id: str) -> dict:
        """Get a playlist by ID.

        Args:
            playlist_id: Spotify playlist ID.

        Returns:
            Playlist resource dict.
        """
        return self._get(f"/playlists/{playlist_id}")

    def create_playlist(
        self,
        user_id: str,
        name: str,
        description: str = "",
        public: bool = True,
    ) -> dict:
        """Create a new playlist.

        Args:
            user_id:     Spotify user ID.
            name:        Playlist name.
            description: Playlist description.
            public:      Whether the playlist is public.

        Returns:
            Created playlist resource dict.
        """
        return self._post(
            f"/users/{user_id}/playlists",
            json={"name": name, "description": description, "public": public},
        )

    def add_to_playlist(self, playlist_id: str, uris: list[str]) -> dict:
        """Add tracks to a playlist.

        Args:
            playlist_id: Spotify playlist ID.
            uris:        List of Spotify track URIs (e.g. "spotify:track:xxx").

        Returns:
            Snapshot ID dict.
        """
        return self._post(f"/playlists/{playlist_id}/tracks", json={"uris": uris})

    def remove_from_playlist(self, playlist_id: str, uris: list[str]) -> dict:
        """Remove tracks from a playlist.

        Args:
            playlist_id: Spotify playlist ID.
            uris:        List of Spotify track URIs.

        Returns:
            Snapshot ID dict.
        """
        tracks = [{"uri": uri} for uri in uris]
        return self._delete(f"/playlists/{playlist_id}/tracks", json={"tracks": tracks})

    # -- Playback (requires Premium + active device) -----------------------

    def get_currently_playing(self) -> dict | None:
        """Get the currently playing track.

        Returns:
            Currently playing dict, or None if nothing is playing.
        """
        resp = self.session.get(f"{_API_BASE}/me/player/currently-playing")
        if resp.status_code == 204:
            return None
        resp.raise_for_status()
        return resp.json()

    def pause(self) -> None:
        """Pause playback on the active device."""
        resp = self.session.put(f"{_API_BASE}/me/player/pause")
        resp.raise_for_status()

    def play(self, uris: list[str] | None = None) -> None:
        """Start or resume playback.

        Args:
            uris: Optional list of track URIs to play.
        """
        body = {}
        if uris:
            body["uris"] = uris
        resp = self.session.put(f"{_API_BASE}/me/player/play", json=body or None)
        resp.raise_for_status()

    def skip_to_next(self) -> None:
        """Skip to the next track."""
        resp = self.session.post(f"{_API_BASE}/me/player/next")
        resp.raise_for_status()

    # -- internal helpers --------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()

    def _delete(self, path: str, **kwargs) -> dict:
        resp = self.session.delete(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
