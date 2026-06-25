"""Werkzeuge (Tool-Use), die Jarvis zur Steuerung des Smart Homes nutzen kann."""

from __future__ import annotations

import json
from typing import Any

from .home_assistant import HomeAssistantError, get_home_assistant

# Schema der Tools, das an die Claude-API übergeben wird.
TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_smart_home_devices",
        "description": (
            "Listet die Smart-Home-Geräte aus Home Assistant samt aktuellem Zustand "
            "(an/aus, Temperatur usw.) auf. Vor dem Schalten nutzen, um die korrekte "
            "entity_id und den aktuellen Status zu kennen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "Optionaler Filter auf einen Gerätetyp (Home-Assistant-Domain), "
                        "z.B. 'light', 'switch', 'climate', 'cover', 'media_player', "
                        "'sensor', 'scene'. Leer lassen für alle Geräte."
                    ),
                }
            },
            "required": [],
        },
    },
    {
        "name": "control_smart_home_device",
        "description": (
            "Steuert ein Smart-Home-Gerät über Home Assistant, indem ein Service "
            "aufgerufen wird (z.B. Licht an/aus, Szene aktivieren, Thermostat setzen). "
            "Immer eine gültige entity_id verwenden – zuvor ggf. "
            "list_smart_home_devices aufrufen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service-Domain, z.B. 'light', 'switch', 'climate', 'scene'.",
                },
                "service": {
                    "type": "string",
                    "description": (
                        "Auszuführender Service, z.B. 'turn_on', 'turn_off', 'toggle', "
                        "'set_temperature', 'turn_on' (für scene)."
                    ),
                },
                "entity_id": {
                    "type": "string",
                    "description": "Ziel-Entität, z.B. 'light.wohnzimmer'.",
                },
                "parameters": {
                    "type": "object",
                    "description": (
                        "Optionale Zusatzparameter für den Service, z.B. "
                        "{'brightness_pct': 60} oder {'temperature': 21}."
                    ),
                },
            },
            "required": ["domain", "service", "entity_id"],
        },
    },
]


async def execute_tool(name: str, tool_input: dict[str, Any]) -> str:
    """Führt ein Tool aus und gibt das Ergebnis als String zurück (für Claude)."""
    ha = get_home_assistant()
    try:
        if name == "list_smart_home_devices":
            domain = tool_input.get("domain") or None
            devices = await ha.get_states(domain=domain)
            if not devices:
                return "Keine passenden Geräte gefunden."
            return json.dumps(devices, ensure_ascii=False)

        if name == "control_smart_home_device":
            domain = tool_input["domain"]
            service = tool_input["service"]
            entity_id = tool_input["entity_id"]
            params = tool_input.get("parameters") or {}
            data = {"entity_id": entity_id, **params}
            await ha.call_service(domain, service, data)
            return (
                f"Erledigt: {domain}.{service} für {entity_id} "
                f"(Parameter: {params or 'keine'})."
            )

        return f"Unbekanntes Tool: {name}"
    except HomeAssistantError as exc:
        return f"Fehler bei der Smart-Home-Steuerung: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Unerwarteter Fehler im Tool '{name}': {exc}"
