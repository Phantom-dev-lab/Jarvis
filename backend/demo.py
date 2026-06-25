"""Demo-Modus: Jarvis-Antworten OHNE API-Key.

Greift nur, wenn kein ANTHROPIC_API_KEY gesetzt ist. Dann reagiert Jarvis
regelbasiert in seiner Rolle und steuert ein *simuliertes* Smart Home, damit
man die Oberfläche und den Ablauf ausprobieren kann, ohne etwas einzurichten.

Für das volle "Superhirn" wird ein echter Claude-API-Key benötigt.
"""

from __future__ import annotations

import datetime as _dt
import re

# Simuliertes Smart Home (nur im Demo-Modus, im Speicher).
_DEMO_HOME: dict[str, dict] = {
    "wohnzimmer": {"name": "Wohnzimmer", "on": False},
    "küche": {"name": "Küche", "on": True},
    "schlafzimmer": {"name": "Schlafzimmer", "on": False},
    "büro": {"name": "Büro", "on": False},
}

_GREETING = (
    "Guten Tag, Sir. J.A.R.V.I.S. im Demo-Modus zu Diensten. "
    "Mein vollständiges Superhirn ist noch offline – dafür fehlt der "
    "ANTHROPIC_API_KEY. Vorführen kann ich mich aber bereits: Fragen Sie nach "
    "der Uhrzeit oder bitten Sie mich, das Licht zu schalten."
)


def _find_room(text: str) -> str | None:
    for key in _DEMO_HOME:
        if key in text or _DEMO_HOME[key]["name"].lower() in text:
            return key
    return None


def _lights_summary() -> str:
    parts = [
        f"{d['name']}: {'an' if d['on'] else 'aus'}" for d in _DEMO_HOME.values()
    ]
    return "; ".join(parts)


def demo_reply(message: str) -> str:
    text = message.lower().strip()

    # Begrüßung
    if re.search(r"\b(hallo|hi|hey|guten (tag|morgen|abend)|servus|moin)\b", text):
        return _GREETING

    # Identität
    if re.search(r"(wer bist du|was bist du|stell dich vor|wie heißt du)", text):
        return (
            "Ich bin J.A.R.V.I.S. – Just A Rather Very Intelligent System –, Ihr "
            "persönlicher Assistent nach dem Vorbild von Tony Starks KI. Aktuell "
            "laufe ich im Demo-Modus. Mit hinterlegtem API-Key stehe ich Ihnen mit "
            "vollem Verstand und Zugriff auf Ihr Smart Home zur Seite."
        )

    # Uhrzeit / Datum
    if re.search(r"(uhrzeit|wie spät|spät|datum|welcher tag)", text):
        now = _dt.datetime.now()
        return (
            f"Es ist {now:%H:%M} Uhr am {now:%d.%m.%Y}, Sir. "
            "Darf ich sonst noch behilflich sein?"
        )

    # Smart-Home-Status
    if re.search(r"(status|welche (geräte|lichter)|was ist an|übersicht)", text):
        return f"Aktueller Zustand der Beleuchtung – {_lights_summary()}."

    # Licht steuern
    if "licht" in text or "lampe" in text or "beleuchtung" in text:
        turn_on = bool(re.search(r"\b(an|ein|einschalt|anschalt|leucht)\b", text))
        turn_off = bool(re.search(r"\b(aus|ausschalt|abschalt|dunkel)\b", text))
        room = _find_room(text)

        if room is None:
            return (
                "In welchem Raum, Sir? Verfügbar sind Wohnzimmer, Küche, "
                "Schlafzimmer und Büro."
            )
        if not turn_on and not turn_off:
            return f"Soll ich das Licht im {_DEMO_HOME[room]['name']} ein- oder ausschalten?"

        _DEMO_HOME[room]["on"] = turn_on
        zustand = "eingeschaltet" if turn_on else "ausgeschaltet"
        return (
            f"Erledigt, Sir. Das Licht im {_DEMO_HOME[room]['name']} ist nun {zustand}. "
            "(Simuliert – mit echtem Home Assistant schalte ich das reale Gerät.)"
        )

    # Dank
    if re.search(r"(danke|vielen dank|merci)", text):
        return "Stets zu Diensten, Sir."

    # Fallback
    return (
        "Im Demo-Modus ist mein Repertoire begrenzt, Sir. Ausprobieren können Sie: "
        "Begrüßung, „Wer bist du?“, „Wie spät ist es?“, „Status der Lichter“ sowie "
        "„Schalte das Licht im Wohnzimmer ein/aus“. Für freie Unterhaltung und mein "
        "volles Können hinterlegen Sie bitte einen ANTHROPIC_API_KEY."
    )
