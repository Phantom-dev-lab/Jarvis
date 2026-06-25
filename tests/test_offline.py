"""Offline-Integrationstest für Jarvis.

Beweist die komplette Logik OHNE echten API-Key und OHNE echtes Home Assistant:
- Claude wird durch einen Fake ersetzt, der einen Tool-Aufruf und danach eine
  finale Textantwort liefert.
- Home Assistant wird durch einen Fake ersetzt, der Geräte zurückgibt und
  Service-Aufrufe protokolliert.

So lässt sich die Chat -> Tool-Use -> Geräte-Steuerung-Schleife verifizieren.

Aufruf:  python -m tests.test_offline
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import backend.home_assistant as ha_module
import backend.jarvis as jarvis_module
from backend.jarvis import Jarvis


# ── Fake Home Assistant ────────────────────────────────────────────────
class FakeHomeAssistant:
    def __init__(self) -> None:
        self.enabled = True
        self.calls: list[tuple] = []
        self._devices = [
            {"entity_id": "light.wohnzimmer", "state": "off", "name": "Wohnzimmer"},
            {"entity_id": "light.kueche", "state": "on", "name": "Küche"},
        ]

    async def get_states(self, domain=None):
        if domain:
            return [d for d in self._devices if d["entity_id"].startswith(f"{domain}.")]
        return self._devices

    async def call_service(self, domain, service, data=None):
        self.calls.append((domain, service, data))
        return {"ok": True}


# ── Fake Claude ────────────────────────────────────────────────────────
class FakeMessages:
    """Liefert beim 1. Aufruf einen Tool-Use, beim 2. eine finale Textantwort."""

    def __init__(self) -> None:
        self.turn = 0

    async def create(self, **kwargs):
        self.turn += 1
        if self.turn == 1:
            tool_block = SimpleNamespace(
                type="tool_use",
                id="toolu_test_1",
                name="control_smart_home_device",
                input={
                    "domain": "light",
                    "service": "turn_on",
                    "entity_id": "light.wohnzimmer",
                    "parameters": {"brightness_pct": 60},
                },
            )
            return SimpleNamespace(stop_reason="tool_use", content=[tool_block])
        text_block = SimpleNamespace(
            type="text",
            text="Erledigt, Sir. Das Licht im Wohnzimmer leuchtet nun mit 60 %.",
        )
        return SimpleNamespace(stop_reason="end_turn", content=[text_block])


class FakeAnthropic:
    def __init__(self) -> None:
        self.messages = FakeMessages()


# ── Test ───────────────────────────────────────────────────────────────
def main() -> int:
    fake_ha = FakeHomeAssistant()
    ha_module._client = fake_ha  # execute_tool nutzt get_home_assistant()

    jarvis = Jarvis.__new__(Jarvis)
    jarvis._settings = jarvis_module.get_settings()
    jarvis._client = FakeAnthropic()

    history = [{"role": "user", "content": "Schalte das Wohnzimmerlicht auf 60 Prozent."}]
    reply = asyncio.run(jarvis.respond(history))

    print("Antwort von Jarvis:", reply)
    print("Home-Assistant-Aufrufe:", fake_ha.calls)

    ok = True

    if not fake_ha.calls:
        print("FEHLER: Es wurde kein Home-Assistant-Service aufgerufen.")
        ok = False
    else:
        domain, service, data = fake_ha.calls[0]
        if (domain, service) != ("light", "turn_on"):
            print(f"FEHLER: Falscher Service aufgerufen: {domain}.{service}")
            ok = False
        if data.get("entity_id") != "light.wohnzimmer":
            print(f"FEHLER: Falsche Entität: {data}")
            ok = False
        if data.get("brightness_pct") != 60:
            print(f"FEHLER: Parameter nicht durchgereicht: {data}")
            ok = False

    if "Wohnzimmer" not in reply:
        print("FEHLER: Finale Textantwort fehlt oder unerwartet.")
        ok = False

    print("\n" + ("✅ ALLE TESTS BESTANDEN" if ok else "❌ TESTS FEHLGESCHLAGEN"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
