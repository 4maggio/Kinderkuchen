# RaspiGui — Kid Launcher for Raspberry Pi

Kinderfreundlicher, icon-basierter Launcher für Raspberry Pi mit 7" Touchscreen.

## 🚀 Schnell-Installation für Raspberry Pi

**Einfache Installation auf DietPi oder Raspberry Pi OS:**

**Variante 1: Mit Git (empfohlen)**
```bash
git clone https://github.com/4maggio/Kinderkuchen.git
cd Kinderkuchen
sudo bash install.sh
```

**Variante 2: Ohne Git (ZIP-Download)**
```bash
# Falls 7zip nicht vorhanden, zuerst installieren:
sudo apt-get install 7zip

# Download und Entpacken:
wget https://github.com/4maggio/Kinderkuchen/archive/refs/heads/main.zip
7z x main.zip
cd Kinderkuchen-main
sudo bash install.sh
```

Das interaktive Installations-Skript richtet automatisch ein:
- ✅ Python 3 + Virtual Environment
- ✅ Minimales X11 und Openbox
- ✅ PyQt5 (System-Paket, ~25MB)
- ❓ Chromium (~200MB, empfohlen für Web-Apps)
- ❓ RealVNC (~20MB, optional für Fernzugriff)
- ❓ On-Screen Keyboard (~5MB, optional für Touch-Eingabe)
- ✅ Auto-Boot beim Systemstart
- ✅ Display-Konfiguration für 7" Touchscreen

**Speicherbedarf:** Minimal ~120MB, Empfohlen ~580MB (alle Features)

**Detaillierte Anleitung:** Siehe [INSTALL.md](INSTALL.md)

---

## Beschreibung

- **Vollbild-Launcher** in Python 3 + PyQt5 für Touchscreen (800x480)
- **Kinderfreundliche Apps:** Chromium im Kiosk-Modus, Python-Apps
- **Optimiert für Raspberry Pi 2** mit minimalem Ressourcen-Verbrauch
- **Eltern-Einstellungen** mit PIN-Schutz für Konfiguration

---

## Entwicklung (Lokal)

1. **Virtual Environment erstellen:**
```bash
python -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
```

2. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

3. **App starten (Fenster-Modus):**
```bash
python apps/week_calendar/main.py --windowed
```

---

## Deployment auf Raspberry Pi

**Automatische Installation:** Nutze `install.sh` (siehe oben)

**Manuelle Installation:** Siehe [Deploy_Instructions.md](Deploy_Instructions.md)

---

## Projektstruktur

```
RaspiGui/
├── apps/
│   └── week_calendar/      # Haupt-Kalender-App
│       ├── main.py          # Entry Point
│       ├── views/           # Dashboard, Kalender-Ansichten
│       ├── widgets/         # Einstellungen, Navigation
│       ├── models/          # Datenbank
│       └── themes/          # Theme-System
├── install.sh              # Automatisches Setup-Skript
├── uninstall.sh            # Deinstallations-Skript
├── requirements.txt        # Python-Dependencies
└── INSTALL.md              # Detaillierte Installations-Anleitung
```

---

## Features

- 📅 **Wochen-Kalender** mit Tages-, Wochen-, Monats- und Jahresansicht
- 🎨 **Anpassbare Themes** mit verschiedenen Farbschemata
- ⏱️ **Bildschirmzeit-Management** mit Timer und Limits
- 🌤️ **Wetter-Integration** mit Open-Meteo API
- 🖼️ **Dekorative Artwork** (optional, austauschbar)
- 🌐 **Multi-Language** (Deutsch, Englisch)
- 🔒 **Eltern-Einstellungen** PIN-geschützt
- 🖥️ **VNC-Unterstützung** für Fernzugriff

---

Lizenz
- Standard: MIT (siehe `LICENSE`). Bitte anpassen falls gewünscht.

Contributing
- Siehe `CONTRIBUTING.md` und `CODE_OF_CONDUCT.md`.

Kontakt / Maintainer
- Siehe Repository-Metadaten oder Issues.
