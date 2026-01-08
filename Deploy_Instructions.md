## Deployment auf Raspberry Pi (DietPi / Raspbian)

**⚠️ HINWEIS: Für automatische Installation siehe [INSTALL.md](INSTALL.md)**

Diese Anleitung ist für manuelle Installation. Für einfache Installation verwende:
```bash
sudo bash install.sh
```

---

### Manuelle Installation (falls automatisches Skript nicht gewünscht)

1) Systemvoraussetzungen
- Raspbian / DietPi mit X11 und touchscreen-Treiber
- Python 3.7+

2) Pakete auf dem Pi installieren (Debian/DietPi):

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
	python3-pyqt5 chromium-browser openbox xinit x11-xserver-utils unclutter
```

3) Dateien auf das Pi kopieren

```bash
# auf dem Entwicklerrechner
scp -r ./* dietpi@raspberrypi:/home/dietpi/kidlauncher

# Oder direkt auf dem Pi klonen:
cd ~
git clone https://github.com/4maggio/Kinderkuchen.git kidlauncher
```

4) Installation und virtuelle Umgebung auf dem Pi

```bash
ssh dietpi@raspberrypi
cd /home/dietpi/kidlauncher
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

5) Service für Autostart (systemd)

Erstelle `/etc/systemd/system/kidlauncher.service` mit folgendem Inhalt:

```ini
[Unit]
Description=Kid Launcher
After=graphical.target

[Service]
Type=simple
User=dietpi
Environment=DISPLAY=:0
WorkingDirectory=/home/dietpi/kidlauncher
ExecStart=/home/dietpi/kidlauncher/venv/bin/python launcher.py
Restart=on-failure

[Install]
WantedBy=graphical.target
```

Dann aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kidlauncher.service
```

6) Hinweise
- Icons sollten 128x128 PNG sein.
- Touch-Kalibrierung: bei Bedarf `display_rotate` in `/boot/config.txt` anpassen.
- Ressourcen: Behalte RAM im Auge (Pi2 ~1GB). Verwende `htop`.

7) Troubleshooting
- Logs: `journalctl -u kidlauncher.service -b`
- Test lokal: `python launcher.py --windowed`