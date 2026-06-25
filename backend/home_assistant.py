"""Schmaler Client für die Home Assistant REST-API.

Doku: https://developers.home-assistant.io/docs/api/rest/
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


class HomeAssistantError(RuntimeError):
    """Wird ausgelöst, wenn ein HA-Aufruf fehlschlägt."""


class HomeAssistantClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.home_assistant_url.rstrip("/")
        self._token = settings.home_assistant_token
        self._enabled = settings.home_assistant_ready

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self._enabled:
            raise HomeAssistantError(
                "Home Assistant ist nicht konfiguriert. Bitte HOME_ASSISTANT_URL "
                "und HOME_ASSISTANT_TOKEN in der .env setzen."
            )
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.request(
                    method, url, headers=self._headers(), **kwargs
                )
                resp.raise_for_status()
                if resp.headers.get("content-type", "").startswith("application/json"):
                    return resp.json()
                return resp.text
        except httpx.HTTPStatusError as exc:  # noqa: PERF203
            raise HomeAssistantError(
                f"Home Assistant antwortete mit {exc.response.status_code}: "
                f"{exc.response.text[:300]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise HomeAssistantError(
                f"Home Assistant nicht erreichbar ({exc!s}). URL prüfen."
            ) from exc

    async def ping(self) -> bool:
        """Schneller Verbindungstest gegen /api/."""
        try:
            await self._request("GET", "/api/")
            return True
        except HomeAssistantError:
            return False

    async def get_states(self, domain: str | None = None) -> list[dict[str, Any]]:
        """Alle Entitäts-Zustände, optional auf eine Domain (z.B. 'light') gefiltert."""
        states = await self._request("GET", "/api/states")
        result = []
        for state in states:
            entity_id = state.get("entity_id", "")
            if domain and not entity_id.startswith(f"{domain}."):
                continue
            result.append(
                {
                    "entity_id": entity_id,
                    "state": state.get("state"),
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                }
            )
        return result

    async def call_service(
        self, domain: str, service: str, data: dict[str, Any] | None = None
    ) -> Any:
        """Ruft einen HA-Service auf, z.B. domain='light', service='turn_on'."""
        payload = data or {}
        return await self._request(
            "POST", f"/api/services/{domain}/{service}", json=payload
        )


_client: HomeAssistantClient | None = None


def get_home_assistant() -> HomeAssistantClient:
    global _client
    if _client is None:
        _client = HomeAssistantClient()
    return _client
