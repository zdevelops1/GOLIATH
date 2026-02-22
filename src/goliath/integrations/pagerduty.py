"""
PagerDuty Integration — manage incidents, services, and on-call schedules via the PagerDuty API.

SETUP INSTRUCTIONS
==================

1. Log in to PagerDuty at https://app.pagerduty.com/

2. Go to Integrations > Developer Tools > API Access Keys
   (or https://your-subdomain.pagerduty.com/api_keys).

3. Create a new REST API Key (General Access Token or User Token).

4. Copy the key and add it to your .env:
     PAGERDUTY_API_KEY=your-api-key
     PAGERDUTY_FROM_EMAIL=your-email@example.com

IMPORTANT NOTES
===============
- API docs: https://developer.pagerduty.com/docs/
- Rate limit: 960 requests per minute per account.
- Authentication: Token token=<key> in Authorization header.
- Base URL: https://api.pagerduty.com

Usage:
    from goliath.integrations.pagerduty import PagerDutyClient

    pd = PagerDutyClient()

    # List incidents
    incidents = pd.list_incidents()

    # Get incident details
    incident = pd.get_incident("P1234AB")

    # Create an incident
    pd.create_incident(
        title="Production database down",
        service_id="PSVC123",
        urgency="high",
    )

    # Acknowledge an incident
    pd.update_incident("P1234AB", status="acknowledged")

    # Resolve an incident
    pd.update_incident("P1234AB", status="resolved")

    # List services
    services = pd.list_services()

    # List on-call users
    oncalls = pd.list_oncalls()
"""

import requests

from goliath import config

_API_BASE = "https://api.pagerduty.com"


class PagerDutyClient:
    """PagerDuty REST API client for incidents, services, and on-call."""

    def __init__(self):
        if not config.PAGERDUTY_API_KEY:
            raise RuntimeError(
                "PAGERDUTY_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/pagerduty.py for setup instructions."
            )

        self._from_email = getattr(config, "PAGERDUTY_FROM_EMAIL", "") or ""

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token token={config.PAGERDUTY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
        })
        if self._from_email:
            self.session.headers["From"] = self._from_email

    # -- Incidents -------------------------------------------------------------

    def list_incidents(
        self,
        statuses: list[str] | None = None,
        sort_by: str = "created_at:desc",
        limit: int = 25,
    ) -> list[dict]:
        """List incidents.

        Args:
            statuses: Filter by statuses (["triggered", "acknowledged", "resolved"]).
            sort_by:  Sort field and direction.
            limit:    Max results.

        Returns:
            List of incident dicts.
        """
        params: dict = {"sort_by": sort_by, "limit": limit}
        if statuses:
            params["statuses[]"] = statuses
        data = self._get("/incidents", params=params)
        return data.get("incidents", [])

    def get_incident(self, incident_id: str) -> dict:
        """Get incident details.

        Args:
            incident_id: Incident ID (e.g. "P1234AB").

        Returns:
            Incident dict.
        """
        data = self._get(f"/incidents/{incident_id}")
        return data.get("incident", {})

    def create_incident(
        self,
        title: str,
        service_id: str,
        urgency: str = "high",
        body: str | None = None,
    ) -> dict:
        """Create an incident.

        Args:
            title:      Incident title.
            service_id: Service ID to trigger.
            urgency:    "high" or "low".
            body:       Incident body / details.

        Returns:
            Created incident dict.
        """
        incident: dict = {
            "type": "incident",
            "title": title,
            "service": {"id": service_id, "type": "service_reference"},
            "urgency": urgency,
        }
        if body:
            incident["body"] = {"type": "incident_body", "details": body}

        data = self._post("/incidents", json={"incident": incident})
        return data.get("incident", data)

    def update_incident(self, incident_id: str, **kwargs) -> dict:
        """Update an incident (acknowledge, resolve, reassign, etc.).

        Args:
            incident_id: Incident ID.
            kwargs:      Fields to update (status, urgency, title, etc.).

        Returns:
            Updated incident dict.
        """
        incident = {"id": incident_id, "type": "incident_reference", **kwargs}
        resp = self.session.put(
            f"{_API_BASE}/incidents/{incident_id}",
            json={"incident": incident},
        )
        resp.raise_for_status()
        return resp.json().get("incident", {})

    # -- Services --------------------------------------------------------------

    def list_services(self, query: str | None = None, limit: int = 25) -> list[dict]:
        """List services.

        Args:
            query: Filter by name substring.
            limit: Max results.

        Returns:
            List of service dicts.
        """
        params: dict = {"limit": limit}
        if query:
            params["query"] = query
        data = self._get("/services", params=params)
        return data.get("services", [])

    def get_service(self, service_id: str) -> dict:
        """Get service details.

        Args:
            service_id: Service ID.

        Returns:
            Service dict.
        """
        data = self._get(f"/services/{service_id}")
        return data.get("service", {})

    # -- On-Call ---------------------------------------------------------------

    def list_oncalls(
        self,
        schedule_ids: list[str] | None = None,
        limit: int = 25,
    ) -> list[dict]:
        """List current on-call entries.

        Args:
            schedule_ids: Filter by schedule IDs.
            limit:        Max results.

        Returns:
            List of on-call dicts.
        """
        params: dict = {"limit": limit}
        if schedule_ids:
            params["schedule_ids[]"] = schedule_ids
        data = self._get("/oncalls", params=params)
        return data.get("oncalls", [])

    # -- Escalation Policies ---------------------------------------------------

    def list_escalation_policies(self, limit: int = 25) -> list[dict]:
        """List escalation policies.

        Args:
            limit: Max results.

        Returns:
            List of escalation policy dicts.
        """
        data = self._get("/escalation_policies", params={"limit": limit})
        return data.get("escalation_policies", [])

    # -- internal helpers ------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, **kwargs) -> dict:
        resp = self.session.post(f"{_API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()
