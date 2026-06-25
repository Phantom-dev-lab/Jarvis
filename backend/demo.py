"""Demo-Modus: Jarvis-Antworten OHNE API-Key.

Greift nur, wenn kein ANTHROPIC_API_KEY gesetzt ist. Dann reagiert Jarvis
regelbasiert in seiner Rolle und steuert ein *simuliertes* Smart Home, damit
man die Oberfläche und den Ablauf ausprobieren kann, ohne etwas einzurichten.

Für das volle "Superhirn" (freie Unterhaltung, echtes Home Assistant) wird ein
echter Claude-API-Key benötigt.
"""

from __future__ import annotations

import datetime as _dt
import random
import re

# ── Simulierter Zustand (nur im Demo-Modus, im Speicher) ───────────────
_LIGHTS: dict[str, dict] = {
    "wohnzimmer": {"name": "Wohnzimmer", "on": False},
    "küche": {"name": "Küche", "on": True},
    "schlafzimmer": {"name": "Schlafzimmer", "on": False},
    "büro": {"name": "Büro", "on": False},
    "bad": {"name": "Bad", "on": False},
}

_CLIMATE: dict[str, dict] = {
    "wohnzimmer": {"name": "Wohnzimmer", "temp": 21.5},
    "schlafzimmer": {"name": "Schlafzimmer", "temp": 19.0},
}

_COVERS: dict[str, dict] = {
    "wohnzimmer": {"name": "Wohnzimmer", "open": True},
    "schlafzimmer": {"name": "Schlafzimmer", "open": False},
}

_MEDIA = {"playing": False, "track": "Back In Black – AC/DC"}

_TIMERS: list[dict] = []

_QUOTES = [
    "„Manchmal muss man rennen, bevor man laufen kann.“ – Tony Stark",
    "„Ich bin Iron Man.“ Aber Sie, Sir, sind das Genie dahinter.",
    "Geduld, Sir – auch ein Arc-Reaktor wurde nicht an einem Tag gebaut.",
    "Wie Mr. Stark zu sagen pflegte: Wenn man scheitert, scheitert man großartig.",
]

_ROOMS_TEXT = "Wohnzimmer, Küche, Schlafzimmer, Büro und Bad"


# ── Hilfsfunktionen ────────────────────────────────────────────────────
def _find_room(text: str, table: dict) -> str | None:
    for key, val in table.items():
        if key in text or val["name"].lower() in text:
            return key
    return None


def _lights_summary() -> str:
    return "; ".join(
        f"{d['name']}: {'an' if d['on'] else 'aus'}" for d in _LIGHTS.values()
    )


def _safe_math(expr: str) -> str | None:
    """Wertet einfache Rechenausdrücke sicher aus (nur Zahlen & + - * / ( ) )."""
    cleaned = expr.replace("x", "*").replace("÷", "/").replace(",", ".")
    if not re.fullmatch(r"[\d\s+\-*/().]+", cleaned):
        return None
    if not re.search(r"\d[\s]*[+\-*/]", cleaned):
        return None
    try:
        result = eval(cleaned, {"__builtins__": {}}, {})  # noqa: S307
    except Exception:  # noqa: BLE001
        return None
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return str(result)


def _weather() -> str:
    conditions = ["heiter", "leicht bewölkt", "sonnig", "wechselhaft"]
    temp = random.randint(14, 24)
    return (
        f"Simulierte Wetterdaten, Sir: aktuell {random.choice(conditions)} bei "
        f"{temp} °C. Mit einem hinterlegten Wetter-Dienst liefere ich echte Werte."
    )


# ── Hauptlogik ─────────────────────────────────────────────────────────
def demo_reply(message: str) -> str:
    text = message.lower().strip()

    # Begrüßung
    if re.search(r"\b(hallo|hi|hey|guten (tag|morgen|abend)|servus|moin|jarvis)\b", text) \
            and len(text) < 30:
        return (
            "Guten Tag, Sir. J.A.R.V.I.S. im Demo-Modus zu Diensten. Mein volles "
            "Superhirn ist offline (kein API-Key), doch ich kann bereits einiges "
            "vorführen. Sagen Sie „Was kannst du?“ für eine Übersicht."
        )

    # Hilfe / Fähigkeiten
    if re.search(r"(was kannst du|hilfe|fähigkeit|kommandos|befehle|help|menü)", text):
        return (
            "Im Demo-Modus stehe ich Ihnen mit Folgendem zur Verfügung, Sir:\n"
            "• 💡 Licht: „Schalte das Licht im Büro ein“, „Alle Lichter aus“\n"
            "• 🌡️ Heizung: „Stelle das Wohnzimmer auf 22 Grad“\n"
            "• 🪟 Rollläden: „Fahre die Rollläden im Schlafzimmer hoch/runter“\n"
            "• 🎵 Musik: „Spiele Musik“ / „Stopp die Musik“\n"
            "• 📋 Status: „Status“ oder „Welche Geräte sind an?“\n"
            "• ⏱️ Timer: „Stelle einen Timer auf 5 Minuten“\n"
            "• 🌦️ Wetter, 🧮 Rechnen, 🕐 Uhrzeit, und der eine oder andere Stark-Spruch.\n"
            "Für freie Unterhaltung hinterlegen Sie bitte einen ANTHROPIC_API_KEY."
        )

    # Identität
    if re.search(r"(wer bist du|was bist du|stell dich vor|wie heißt du)", text):
        return (
            "Ich bin J.A.R.V.I.S. – Just A Rather Very Intelligent System –, Ihr "
            "persönlicher Assistent nach dem Vorbild von Tony Starks KI. Derzeit im "
            "Demo-Modus; mit API-Key stehe ich Ihnen mit vollem Verstand zur Seite."
        )

    # Uhrzeit / Datum
    if re.search(r"(uhrzeit|wie spät|wieviel uhr|datum|welcher tag|welches datum)", text):
        now = _dt.datetime.now()
        return f"Es ist {now:%H:%M} Uhr am {now:%A, %d.%m.%Y}, Sir."

    # Gesamtstatus
    if re.search(r"(status|welche (geräte|lichter)|was ist an|übersicht|zustand)", text):
        klima = "; ".join(f"{c['name']}: {c['temp']:.1f} °C" for c in _CLIMATE.values())
        musik = f"läuft ({_MEDIA['track']})" if _MEDIA["playing"] else "aus"
        return (
            f"Systemübersicht, Sir:\n"
            f"💡 Licht – {_lights_summary()}\n"
            f"🌡️ Heizung – {klima}\n"
            f"🎵 Musik – {musik}"
        )

    # Alle Lichter
    if re.search(r"alle? licht", text):
        on = bool(re.search(r"\b(an|ein)\b", text))
        for d in _LIGHTS.values():
            d["on"] = on
        return (
            f"Sämtliche Lichter wurden {'eingeschaltet' if on else 'ausgeschaltet'}, Sir."
        )

    # Heizung / Temperatur
    if re.search(r"(heizung|thermostat|temperatur|grad)", text):
        room = _find_room(text, _CLIMATE)
        m = re.search(r"(\d{1,2})(?:[.,](\d))?\s*(?:grad|°)", text)
        if m:
            value = float(m.group(1) + ("." + m.group(2) if m.group(2) else ""))
            target = room or "wohnzimmer"
            _CLIMATE.setdefault(target, {"name": target.capitalize(), "temp": value})
            _CLIMATE[target]["temp"] = value
            return (
                f"Erledigt, Sir. Die Zieltemperatur im {_CLIMATE[target]['name']} steht "
                f"nun bei {value:.1f} °C. (Simuliert.)"
            )
        if room:
            return f"Im {_CLIMATE[room]['name']} sind aktuell {_CLIMATE[room]['temp']:.1f} °C eingestellt."
        klima = "; ".join(f"{c['name']}: {c['temp']:.1f} °C" for c in _CLIMATE.values())
        return f"Aktuelle Heizungssollwerte – {klima}. Auf wie viel Grad darf ich stellen?"

    # Rollläden
    if re.search(r"(rolll?äden|rolll?aden|rollo|jalousie|vorhang|markise)", text):
        room = _find_room(text, _COVERS) or "wohnzimmer"
        if re.search(r"\b(hoch|auf|öffn|rauf)\b", text):
            _COVERS[room]["open"] = True
            return f"Die Rollläden im {_COVERS[room]['name']} sind nun oben, Sir."
        if re.search(r"\b(runter|zu|schließ|rab|herunter)\b", text):
            _COVERS[room]["open"] = False
            return f"Die Rollläden im {_COVERS[room]['name']} sind nun unten, Sir."
        return "Soll ich die Rollläden hoch- oder herunterfahren?"

    # Musik / Medien
    if re.search(r"(musik|song|lied|spiel|abspiel|media|radio)", text):
        if re.search(r"\b(stopp|stop|aus|pause|halt)\b", text):
            _MEDIA["playing"] = False
            return "Musik gestoppt, Sir."
        _MEDIA["playing"] = True
        return f"Ich spiele „{_MEDIA['track']}“, Sir. Viel Vergnügen."

    # Licht
    if re.search(r"(licht|lampe|beleuchtung)", text):
        turn_on = bool(re.search(r"\b(an|ein|einschalt|anschalt|leucht|hell)\b", text))
        turn_off = bool(re.search(r"\b(aus|ausschalt|abschalt|dunkel)\b", text))
        room = _find_room(text, _LIGHTS)
        if room is None:
            return f"In welchem Raum, Sir? Verfügbar: {_ROOMS_TEXT}."
        if not turn_on and not turn_off:
            return f"Soll ich das Licht im {_LIGHTS[room]['name']} ein- oder ausschalten?"
        _LIGHTS[room]["on"] = turn_on
        return (
            f"Erledigt, Sir. Das Licht im {_LIGHTS[room]['name']} ist nun "
            f"{'eingeschaltet' if turn_on else 'ausgeschaltet'}. "
            "(Simuliert – mit echtem Home Assistant schalte ich das reale Gerät.)"
        )

    # Timer
    if re.search(r"(timer|wecker|erinner|countdown)", text):
        m = re.search(r"(\d{1,3})\s*(sekunde|minute|stunde)", text)
        if m:
            amount, unit = m.group(1), m.group(2)
            _TIMERS.append({"amount": amount, "unit": unit})
            return (
                f"Timer über {amount} {unit}n gestellt, Sir. (Simuliert – es ertönt "
                "kein echter Alarm, doch ich habe ihn notiert.)"
            )
        return "Auf wie lange darf ich den Timer stellen, Sir?"

    # Wetter
    if re.search(r"(wetter|regen|sonne|temperatur draußen|kalt|warm draußen)", text):
        return _weather()

    # Rechnen
    math_result = _safe_math(text.replace("rechne", "").replace("wieviel ist", "")
                             .replace("was ist", "").replace("=", "").strip())
    if math_result is not None:
        return f"Das ergibt {math_result}, Sir."

    # Dank
    if re.search(r"(danke|vielen dank|merci|super|klasse)", text):
        return "Stets zu Diensten, Sir."

    # Witz / Spruch
    if re.search(r"(witz|spruch|zitat|motivier|langweilig)", text):
        return random.choice(_QUOTES)

    # Verabschiedung
    if re.search(r"(tschüss|bye|ciao|gute nacht|bis später)", text):
        return "Bis bald, Sir. Ich halte die Systeme bereit."

    # Fallback
    return (
        "Im Demo-Modus ist mein Repertoire begrenzt, Sir. Sagen Sie „Was kannst du?“ "
        "für eine Übersicht – etwa Licht und Heizung steuern, Status abfragen, "
        "rechnen oder die Uhrzeit erfragen. Für freie Unterhaltung und mein volles "
        "Können hinterlegen Sie bitte einen ANTHROPIC_API_KEY."
    )
