# RaspiGui — Kid Launcher for Raspberry Pi

Kurzes, einfaches Icon‑basiertes Launcher-Projekt für Raspberry Pi (PyQt5).

Kurzbeschreibung
- Vollbild‑Launcher geschrieben in Python 3 + PyQt5 für einen Touchscreen (Raspberry Pi 7").
- Startet kinderfreundliche Apps (z. B. Chromium im Kiosk‑Mode, Python‑Apps in `apps/`).

Schnellstart (Entwicklung)
1. Virtuelle Umgebung erstellen:
```bash
python -m venv venv
.
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```
2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```
3. Launcher/Beispiel-App starten (fenstermodus):
```bash
python apps/week_calendar/main.py --windowed
```

Deployment (Raspberry Pi)
- Siehe `Deploy_Instructions.md` für Pi-spezifische Schritte (Installieren von PyQt5, Chromium, Kopieren nach `/opt/kidlauncher/`, Autostart).

Projektstruktur (auszugsweise)
- `apps/` — einzelne Anwendungen (z. B. `week_calendar`)
- `icons/` — Launcher-Icons
- `utils/` — kleine Hilfsmodules
- `Deploy_Instructions.md` — Deploy- & Boot-Integration

Lizenz
- Standard: MIT (siehe `LICENSE`). Bitte anpassen falls gewünscht.

Contributing
- Siehe `CONTRIBUTING.md` und `CODE_OF_CONDUCT.md`.

Kontakt / Maintainer
- Siehe Repository-Metadaten oder Issues.
