"""
Datadog Integration — send metrics, manage monitors, and query events via the Datadog API.

SETUP INSTRUCTIONS
==================

1. Log in to Datadog at https://app.datadoghq.com/

2. Go to Organization Settings > API Keys to get your API key.
   Go to Organization Settings > Application Keys to create an Application key.

3. Add both to your .env:
     DATADOG_API_KEY=your-api-key
     DATADOG_APP_KEY=your-application-key

4. If you use an EU or other regional site, set:
     DATADOG_SITE=datadoghq.eu

IMPORTANT NOTES
===============
- API docs: https://docs.datadoghq.com/api/latest/
- Rate limits vary by endpoint and plan.
- Authentication via DD-API-KEY and DD-APPLICATION-KEY headers.
- Default site: datadoghq.com

Usage:
    from goliath.integrations.datadog import DatadogClient

    dd = DatadogClient()

    # Send a metric
    dd.submit_metric("my.metric", value=42.0, tags=["env:prod"])

    # List monitors
    monitors = dd.list_monitors()

    # Get a monitor
    monitor = dd.get_monitor(12345)

    # Create a monitor
    dd.create_monitor(
        name="High CPU",
        monitor_type="metric alert",
        query="avg(last_5m):avg:system.cpu.user{*} > 90",
    )

    # Mute a monitor
    dd.mute_monitor(12345)

    # Search events
    events = dd.list_events(start=1700000000, end=1700086400)

    # Send an event
    dd.create_event(title="Deploy", text="Deployed v2.1", tags=["env:prod"])
"""

import time

import requests

from goliath import config

_DEFAULT_SITE = "datadoghq.com"


class DatadogClient:
    """Datadog REST API client for metrics, monitors, and events."""

    def __init__(self):
        if not config.DATADOG_API_KEY:
            raise RuntimeError(
                "DATADOG_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/datadog.py for setup instructions."
            )

        site = getattr(config, "DATADOG_SITE", "") or _DEFAULT_SITE
        self.base_url = f"https://api.{site}/api"

        self.session = requests.Session()
        self.session.headers.update({
            "DD-API-KEY": config.DATADOG_API_KEY,
            "DD-APPLICATION-KEY": getattr(config, "DATADOG_APP_KEY", "") or "",
            "Content-Type": "application/json",
        })

    # -- Metrics ---------------------------------------------------------------

    def submit_metric(
        self,
        metric: str,
        value: float,
        metric_type: str = "gauge",
        tags: list[str] | None = None,
        host: str | None = None,
    ) -> dict:
        """Submit a metric data point.

        Args:
            metric:      Metric name (e.g. "my.app.requests").
            value:       Metric value.
            metric_type: Type ("gauge", "count", "rate").
            tags:        List of tags (e.g. ["env:prod", "region:us"]).
            host:        Hostname.

        Returns:
            Submission result.
        """
        now = int(time.time())
        point: dict = {
            "metric": metric,
            "type": _METRIC_TYPE_MAP.get(metric_type, 3),
            "points": [{"timestamp": now, "value": value}],
        }
        if tags:
            point["tags"] = tags
        if host:
            point["resources"] = [{"name": host, "type": "host"}]

        return self._post("/v2/series", json={"series": [point]})

    # -- Monitors --------------------------------------------------------------

    def list_monitors(self, name: str | None = None) -> list[dict]:
        """List monitors.

        Args:
            name: Filter by name substring.

        Returns:
            List of monitor dicts.
        """
        params: dict = {}
        if name:
            params["name"] = name
        return self._get_list("/v1/monitor", params=params)

    def get_monitor(self, monitor_id: int) -> dict:
        """Get monitor details.

        Args:
            monitor_id: Monitor ID.

        Returns:
            Monitor dict.
        """
        return self._get(f"/v1/monitor/{monitor_id}")

    def create_monitor(
        self,
        name: str,
        monitor_type: str,
        query: str,
        message: str = "",
        tags: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Create a monitor.

        Args:
            name:         Monitor name.
            monitor_type: Type (e.g. "metric alert", "service check").
            query:        Monitor query string.
            message:      Notification message (supports @mentions).
            tags:         Monitor tags.
            kwargs:       Additional options (thresholds, priority, etc.).

        Returns:
            Created monitor dict.
        """
        payload: dict = {
            "name": name,
            "type": monitor_type,
            "query": query,
            "message": message,
            **kwargs,
        }
        if tags:
            payload["tags"] = tags
        return self._post("/v1/monitor", json=payload)

    def update_monitor(self, monitor_id: int, **kwargs) -> dict:
        """Update a monitor.

        Args:
            monitor_id: Monitor ID.
            kwargs:     Fields to update.

        Returns:
            Updated monitor dict.
        """
        resp = self.session.put(
            f"{self.base_url}/v1/monitor/{monitor_id}", json=kwargs
        )
        resp.raise_for_status()
        return resp.json()

    def delete_monitor(self, monitor_id: int) -> dict:
        """Delete a monitor.

        Args:
            monitor_id: Monitor ID.

        Returns:
            Deletion result.
        """
        resp = self.session.delete(
            f"{self.base_url}/v1/monitor/{monitor_id}"
        )
        resp.raise_for_status()
        return resp.json()

    def mute_monitor(self, monitor_id: int, end: int | None = None) -> dict:
        """Mute a monitor.

        Args:
            monitor_id: Monitor ID.
            end:        POSIX timestamp when mute should end (omit for indefinite).

        Returns:
            Muted monitor dict.
        """
        payload: dict = {}
        if end is not None:
            payload["end"] = end
        return self._post(f"/v1/monitor/{monitor_id}/mute", json=payload)

    # -- Events ----------------------------------------------------------------

    def list_events(
        self,
        start: int,
        end: int,
        sources: str | None = None,
        tags: str | None = None,
    ) -> list[dict]:
        """List events in a time range.

        Args:
            start:   POSIX start timestamp.
            end:     POSIX end timestamp.
            sources: Comma-separated event sources.
            tags:    Comma-separated tags.

        Returns:
            List of event dicts.
        """
        params: dict = {"start": start, "end": end}
        if sources:
            params["sources"] = sources
        if tags:
            params["tags"] = tags
        data = self._get("/v1/events", params=params)
        return data.get("events", []) if isinstance(data, dict) else data

    def create_event(
        self,
        title: str,
        text: str,
        tags: list[str] | None = None,
        alert_type: str = "info",
    ) -> dict:
        """Create an event.

        Args:
            title:      Event title.
            text:       Event body (supports markdown).
            tags:       Event tags.
            alert_type: "error", "warning", "info", or "success".

        Returns:
            Created event dict.
        """
        payload: dict = {
            "title": title,
            "text": text,
            "alert_type": alert_type,
        }
        if tags:
            payload["tags"] = tags
        data = self._post("/v1/events", json=payload)
        return data.get("event", data) if isinstance(data, dict) else data

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _get_list(self, path: str, **kwargs) -> list[dict]:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        result = resp.json()
        return result if isinstance(result, list) else [result]

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()


# Maps friendly names to Datadog v2 metric type integers.
_METRIC_TYPE_MAP = {"gauge": 3, "count": 1, "rate": 2}
