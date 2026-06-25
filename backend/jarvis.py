"""Das Gehirn: Gesprächslogik mit Claude inkl. Tool-Use für Home Assistant."""

from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from .config import get_settings
from .demo import demo_reply
from .tools import TOOLS, execute_tool

MAX_TOKENS = 2048
MAX_TOOL_TURNS = 6  # Schutz gegen Endlosschleifen


def _system_prompt() -> str:
    settings = get_settings()
    ha = (
        "Du bist mit Home Assistant verbunden und kannst das Smart Home über die "
        "bereitgestellten Tools steuern und abfragen."
        if settings.home_assistant_ready
        else "Home Assistant ist aktuell NICHT konfiguriert. Wenn nach Smart-Home-"
        "Steuerung gefragt wird, weise freundlich darauf hin, dass die Verbindung "
        "noch eingerichtet werden muss."
    )
    return (
        f"Du bist J.A.R.V.I.S., der hochintelligente persönliche Assistent im Stil "
        f"von Tony Starks KI aus Iron Man. Du sprichst {settings.jarvis_language}.\n\n"
        f"Persönlichkeit:\n"
        f"- Du bist ein 'Superhirn': extrem kompetent, präzise, vorausschauend und "
        f"hilfst bei wirklich jeder Aufgabe (Wissen, Planung, Technik, Alltag).\n"
        f"- Stil: höflich, ruhig, leicht britisch-trocken-humorvoll, loyal. Du "
        f"sprichst den Nutzer mit '{settings.jarvis_user_name}' an.\n"
        f"- Antworte klar und auf den Punkt. Keine überflüssigen Floskeln, aber mit "
        f"Charakter. Halte Antworten für die Sprachausgabe natürlich lesbar.\n\n"
        f"Fähigkeiten:\n- {ha}\n"
        f"- Bevor du ein Gerät schaltest, ermittle bei Unsicherheit zunächst die "
        f"korrekte entity_id über das Listen-Tool. Bestätige Aktionen knapp.\n"
        f"- Wenn du etwas nicht sicher weißt, sage es ehrlich, statt zu raten."
    )


class Jarvis:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._client: AsyncAnthropic | None = (
            AsyncAnthropic(api_key=settings.anthropic_api_key)
            if settings.claude_ready
            else None
        )

    @property
    def ready(self) -> bool:
        return self._client is not None

    async def respond(self, history: list[dict[str, Any]]) -> str:
        """Nimmt den bisherigen Gesprächsverlauf und liefert Jarvis' Antworttext.

        `history` ist eine Liste von {'role': 'user'|'assistant', 'content': str|list}.
        Die Tool-Use-Schleife wird intern abgewickelt; zurück kommt reiner Text.
        """
        if self._client is None:
            # Kein API-Key -> regelbasierter Demo-Modus, damit man Jarvis auch
            # ohne Einrichtung ausprobieren kann.
            last_user = next(
                (
                    m["content"]
                    for m in reversed(history)
                    if m.get("role") == "user" and isinstance(m.get("content"), str)
                ),
                "",
            )
            return demo_reply(last_user)

        settings = self._settings
        messages = list(history)

        for _ in range(MAX_TOOL_TURNS):
            response = await self._client.messages.create(
                model=settings.jarvis_model,
                max_tokens=MAX_TOKENS,
                system=_system_prompt(),
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                # Assistant-Turn (inkl. tool_use-Blöcke) übernehmen
                messages.append(
                    {"role": "assistant", "content": response.content}
                )
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await execute_tool(block.name, block.input or {})
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            }
                        )
                messages.append({"role": "user", "content": tool_results})
                continue

            # Normale Textantwort -> zusammensetzen und zurückgeben
            return self._extract_text(response.content)

        return (
            "Verzeihung – ich habe mich in zu vielen Arbeitsschritten verloren. "
            "Bitte formuliere die Anfrage etwas direkter."
        )

    @staticmethod
    def _extract_text(content: list[Any]) -> str:
        parts = [block.text for block in content if getattr(block, "type", "") == "text"]
        return "\n".join(parts).strip() or "…"


_jarvis: Jarvis | None = None


def get_jarvis() -> Jarvis:
    global _jarvis
    if _jarvis is None:
        _jarvis = Jarvis()
    return _jarvis
