# RaspiGui Kid Launcher - Installation Guide

## Schnellstart für DietPi / Raspberry Pi OS

### Voraussetzungen
- Raspberry Pi 2 (oder neuer)
- DietPi oder Raspberry Pi OS (headless oder mit Desktop)
- 7" Touchscreen (800x480) - optional
- Mindestens 2GB freier Speicher
- Internet-Verbindung

### Installation

1. **Repository herunterladen:**

**Methode A: Mit Git (wenn installiert)**
```bash
cd ~
git clone https://github.com/4maggio/Kinderkuchen.git
cd Kinderkuchen
```

**Methode B: Ohne Git - ZIP-Download mit wget (empfohlen wenn Git nicht vorhanden)**
```bash
cd ~

# 7zip installieren (falls nicht vorhanden):
sudo apt-get install 7zip

# Download und Entpacken:
wget https://github.com/4maggio/Kinderkuchen/archive/refs/heads/main.zip
7z x main.zip
cd Kinderkuchen-main
```

**Methode C: Mit curl statt wget**
```bash
cd ~

# 7zip installieren (falls nicht vorhanden):
sudo apt-get install 7zip

# Download und Entpacken:
curl -L https://github.com/4maggio/Kinderkuchen/archive/refs/heads/main.zip -o kinderkuchen.zip
7z x kinderkuchen.zip
cd Kinderkuchen-main
```

**Hinweis:** 7zip wird nur zum Entpacken des Downloads benötigt (~500KB). Das install.sh Skript installiert es nicht, um Speicher zu sparen.

2. **Installations-Skript ausführen:**
```bash
sudo bash install.sh
```

Das Skript wird interaktiv folgendes installieren und konfigurieren:
- ✅ Python 3 + venv
- ✅ Minimales X11 (nur für Chromium)
- ✅ Openbox Window Manager
- ✅ PyQt5 (als System-Paket oder via pip)
- ✅ Chromium Browser (für Kiosk-Modus)
- ✅ RealVNC Server (optional)
- ✅ Auto-Boot Konfiguration
- ✅ Display-Rotation (falls nötig)

**Geschätzte Installationszeit:** 10-30 Minuten (abhängig von Internet-Geschwindigkeit)

**Geschätzter Speicherbedarf:**
- Minimal (ohne VNC): ~350MB
- Mit VNC: ~400MB

3. **Neu starten:**
```bash
sudo reboot
```

Nach dem Neustart startet die App automatisch!

---

## Manuelle Steuerung

### App starten (manuell):
```bash
cd /opt/kidlauncher
./start.sh
```

### App im Fenster-Modus (für Entwicklung):
```bash
cd /opt/kidlauncher
./start.sh --windowed
```

### Systemd Service:
```bash
# Status prüfen
sudo systemctl status kidlauncher

# Starten
sudo systemctl start kidlauncher

# Stoppen
sudo systemctl stop kidlauncher

# Logs anzeigen
sudo journalctl -u kidlauncher -f
```

### Auto-Start deaktivieren:
```bash
sudo systemctl disable kidlauncher
```

### Auto-Start wieder aktivieren:
```bash
sudo systemctl enable kidlauncher
```

---

## Konfiguration

### Eltern-Einstellungen

Öffne in der App das ⚙-Einstellungs-Menü:
- **Standard-PIN:** 1234 (bitte im Sicherheits-Tab ändern!)
- Hier kannst du konfigurieren:
  - Wetter-Standort
  - Themes und Schriftgrößen
  - Bildschirmzeit-Limits
  - Launcher-Apps
  - VNC-Fernzugriff

### Eigene Apps hinzufügen

Im Einstellungs-Menü → Apps-Tab:
1. Klicke auf "+"
2. Wähle:
   - **Python-App:** Pfad zu einer .py Datei
   - **Website:** URL für Chromium Kiosk-Modus

### Display-Rotation ändern

1. Via Einstellungen in der App (wenn möglich)
2. Oder manuell in `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
# Füge hinzu:
display_rotate=2  # 0=normal, 1=90°, 2=180°, 3=270°
```

---

## Deinstallation

```bash
# Service stoppen und deaktivieren
sudo systemctl stop kidlauncher
sudo systemctl disable kidlauncher
sudo rm /etc/systemd/system/kidlauncher.service

# Installation entfernen
sudo rm -rf /opt/kidlauncher

# Auto-Login deaktivieren (optional)
sudo rm /etc/systemd/system/getty@tty1.service.d/autologin.conf

# X11 entfernen (optional - nur wenn nicht mehr benötigt)
sudo apt-get remove --purge xserver-xorg openbox
sudo apt-get autoremove
```

---

## Fehlerbehebung

### App startet nicht nach Neustart

1. Prüfe Service-Status:
```bash
sudo systemctl status kidlauncher
```

2. Prüfe Logs:
```bash
sudo journalctl -u kidlauncher -n 50
```

3. X11 testen:
```bash
# Als dietpi user:
DISPLAY=:0 xset q
```

### Touchscreen funktioniert nicht

1. Prüfe ob Device erkannt wird:
```bash
xinput list
```

2. Kalibrierung (falls nötig):
```bash
sudo apt-get install xinput-calibrator
DISPLAY=:0 xinput_calibrator
```

### Chromium startet nicht

1. X11 läuft:
```bash
ps aux | grep X
```

2. Chromium manuell testen:
```bash
DISPLAY=:0 chromium-browser --version
```

### Performance-Probleme (Pi 2)

1. GPU-Speicher erhöhen in `/boot/config.txt`:
```
gpu_mem=128
```

2. Swap reduzieren:
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=100
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

3. Unnötige Services deaktivieren:
```bash
sudo systemctl disable bluetooth
sudo systemctl disable triggerhappy
```

---

## Entwicklung

### Code bearbeiten:
```bash
cd /opt/kidlauncher/apps/week_calendar
nano main.py
```

### App im Entwicklungs-Modus starten:
```bash
cd /opt/kidlauncher
source venv/bin/activate
python apps/week_calendar/main.py --windowed
```

### Logs live verfolgen:
```bash
sudo journalctl -u kidlauncher -f
```

---

## Ressourcen-Verbrauch

**Typischer Verbrauch (Raspberry Pi 2):**
- **RAM:** 
  - Launcher: ~40MB
  - Mit Chromium: +200-300MB
  - **Gesamt:** ~250-350MB von 1GB

- **CPU:**
  - Idle: ~5%
  - Aktiv: 15-30%

- **Disk:**
  - Installation: ~400MB
  - Daten/Cache: ~50MB

---

## Support & Weitere Infos

- **Projekt:** https://github.com/4maggio/Kinderkuchen
- **Issues:** https://github.com/4maggio/Kinderkuchen/issues
- **Dokumentation:** Siehe `Raspi_Concept` im Repository

---

## Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Weitere Informationen: [LICENSE](LICENSE)
