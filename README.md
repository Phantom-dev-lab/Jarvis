# J.A.R.V.I.S. 🔵

> *Just A Rather Very Intelligent System* — ein persönlicher KI-Assistent im Stil
> von Iron Mans Jarvis. Bedienbar über eine Weboberfläche per **Chat** und
> **Sprache**, angetrieben von Claude (Anthropic) und mit optionaler Anbindung an
> dein **Home Assistant** Smart Home.

![Status](https://img.shields.io/badge/Made%20with-Claude-36d1ff)

---

## ✨ Funktionen

- **Weboberfläche im Jarvis-Look** — dunkles UI mit Arc-Reactor-Animation.
- **Chat** — natürliche Unterhaltung in deiner Sprache.
- **Spracheingabe** (Speech-to-Text) per Mikrofon-Knopf — direkt im Browser.
- **Sprachausgabe** (Text-to-Speech) — Jarvis antwortet hörbar, abschaltbar.
- **„Superhirn"** — nutzt das leistungsstärkste Claude-Modell und unterstützt dich
  bei Wissen, Planung, Technik und Alltag.
- **Smart-Home-Steuerung** — Jarvis kann über **Home Assistant** Lichter, Schalter,
  Szenen, Thermostate u.v.m. abfragen und schalten (Tool-Use).
- **Gesprächsgedächtnis** je Sitzung.

---

## 🚀 Schnellstart

### 1. Voraussetzungen
- Python 3.10+
- Ein **Anthropic API-Key** → https://console.anthropic.com/
- (Optional) Home Assistant mit einem **Long-Lived Access Token**

### 2. Konfigurieren
```bash
cp .env.example .env
# .env öffnen und mindestens ANTHROPIC_API_KEY eintragen
```

### 3. Starten
```bash
./run.sh
```
Das Skript legt eine virtuelle Umgebung an, installiert alles und startet den
Server. Anschließend im Browser öffnen:

> **http://localhost:8000**

> 💡 Spracheingabe/-ausgabe funktioniert am besten in **Google Chrome** und
> benötigt Mikrofon-Freigabe. Für Mikrofonzugriff aus dem Netzwerk wird i.d.R.
> `https` oder `localhost` benötigt.

#### Alternativ manuell
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m backend.main
```

---

## 🏠 Home Assistant einrichten

1. In Home Assistant: **Profil → Sicherheit → Long-lived access tokens →
   „Token erstellen"**.
2. In die `.env` eintragen:
   ```env
   HOME_ASSISTANT_URL=http://homeassistant.local:8123
   HOME_ASSISTANT_TOKEN=dein_token
   ```
3. Server neu starten. In der Kopfzeile sollte „Smart Home verbunden" erscheinen.

Danach genügen Sätze wie:
- *„Schalte das Licht im Wohnzimmer ein."*
- *„Welche Geräte sind gerade an?"*
- *„Aktiviere die Szene Kinoabend."*
- *„Stelle das Thermostat im Schlafzimmer auf 21 Grad."*

Jarvis ermittelt die passende Entität selbst und ruft den richtigen
Home-Assistant-Service auf.

---

## 🧠 Modell anpassen

In der `.env`:
```env
JARVIS_MODEL=claude-opus-4-8      # Standard: maximal leistungsfähig
JARVIS_LANGUAGE=Deutsch
JARVIS_USER_NAME=Sir
```

---

## 🗂 Projektstruktur

```
Jarvis/
├── backend/
│   ├── main.py             # FastAPI-Server + Weboberfläche
│   ├── jarvis.py           # Gesprächslogik mit Claude + Tool-Use-Schleife
│   ├── tools.py            # Smart-Home-Werkzeuge (Tool-Definitionen)
│   ├── home_assistant.py   # Home-Assistant-REST-Client
│   └── config.py           # Konfiguration aus .env
├── frontend/
│   ├── index.html          # Weboberfläche
│   ├── style.css           # Jarvis-Design
│   └── app.js              # Chat, Spracheingabe & -ausgabe
├── requirements.txt
├── run.sh
└── .env.example
```

---

## 🔌 API-Endpunkte

| Methode | Pfad                          | Beschreibung                       |
|--------|-------------------------------|------------------------------------|
| `POST` | `/api/chat`                   | Nachricht senden, Antwort erhalten |
| `POST` | `/api/reset`                  | Gesprächsverlauf zurücksetzen      |
| `GET`  | `/api/health`                 | Status von Kern & Konfiguration    |
| `GET`  | `/api/home-assistant/status`  | Verbindungsstatus zu Home Assistant|

---

## 🔒 Hinweise

- Deine `.env` mit den Keys wird durch `.gitignore` **nicht** eingecheckt.
- Der Gesprächsverlauf wird nur im Arbeitsspeicher gehalten (Einzelnutzer-/
  Heimbetrieb). Bei Bedarf lässt sich das leicht auf eine Datenbank erweitern.
- Für den Zugriff aus dem Internet einen Reverse-Proxy mit HTTPS und
  Authentifizierung davor setzen.

---

*„Manchmal muss man rennen, bevor man laufen kann."* — Tony Stark
