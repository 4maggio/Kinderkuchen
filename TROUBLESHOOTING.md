# Troubleshooting Guide

## Häufige Probleme und Lösungen

### Installation schlägt fehl

#### Problem: "Command not found: git"
**Lösung:**
```bash
sudo apt-get update
sudo apt-get install -y git
```

#### Problem: "No space left on device"
**Lösung:** Speicher aufräumen
```bash
# Zeige Speicherverbrauch
df -h

# Entferne apt Cache
sudo apt-get clean

# Entferne alte Logs
sudo journalctl --vacuum-time=7d

# Finde große Dateien
sudo find / -type f -size +50M 2>/dev/null
```

#### Problem: PyQt5 Installation dauert ewig (via pip)
**Lösung:** System-Paket verwenden
```bash
sudo apt-get install python3-pyqt5 python3-pyqt5.qtwidgets
# Im install.sh "System-Paket verwenden" wählen
```

---

### App startet nicht

#### Problem: Service startet nicht nach Reboot
**Diagnose:**
```bash
sudo systemctl status kidlauncher
sudo journalctl -u kidlauncher -n 50
```

**Häufige Ursachen:**
1. **X11 läuft nicht:**
   ```bash
   ps aux | grep X
   # Falls nicht: startx manuell testen
   ```

2. **Permissions falsch:**
   ```bash
   sudo chown -R dietpi:dietpi /opt/kidlauncher
   ```

3. **Python-Fehler:**
   ```bash
   cd /opt/kidlauncher
   source venv/bin/activate
   python apps/week_calendar/main.py --windowed
   # Prüfe Fehlermeldungen
   ```

#### Problem: "ModuleNotFoundError: No module named 'PyQt5'"
**Lösung:**
```bash
# Prüfe ob PyQt5 im venv ist
cd /opt/kidlauncher
source venv/bin/activate
python -c "import PyQt5; print(PyQt5.__file__)"

# Falls nicht gefunden:
pip install PyQt5
# ODER System-Paket verwenden:
sudo apt-get install python3-pyqt5
```

#### Problem: Schwarzer Bildschirm nach Boot
**Diagnose:**
```bash
# Von SSH aus:
DISPLAY=:0 xset q
# Falls Fehler: X11 läuft nicht

# Check tty1
sudo systemctl status getty@tty1
```

**Lösung:**
```bash
# X11 manuell starten als dietpi user
su - dietpi
startx
```

---

### Display/Touchscreen Probleme

#### Problem: Display ist verkehrt herum
**Lösung:**
```bash
sudo nano /boot/config.txt
# Füge hinzu:
display_rotate=2  # 0=0°, 1=90°, 2=180°, 3=270°

# Oder in App-Einstellungen (falls zugänglich)
```

#### Problem: Touchscreen reagiert nicht
**Diagnose:**
```bash
# Liste Input-Geräte
xinput list

# Test Touch-Events
DISPLAY=:0 xinput test <device-id>
# Touchscreen berühren - Events sollten erscheinen
```

**Lösung:**
```bash
# Falls Device nicht erkannt:
sudo apt-get install xserver-xorg-input-evdev

# Neustart
sudo reboot
```

#### Problem: Touch-Koordinaten falsch
**Lösung:**
```bash
# Kalibrierung
sudo apt-get install xinput-calibrator
DISPLAY=:0 xinput_calibrator

# Output in /etc/X11/xorg.conf.d/99-calibration.conf speichern
```

---

### Performance-Probleme

#### Problem: App ist sehr langsam (Pi 2)
**Optimierungen:**

1. **GPU-Speicher erhöhen:**
   ```bash
   sudo nano /boot/config.txt
   # Ändere:
   gpu_mem=128  # Erhöhe auf 128-256MB
   ```

2. **Swap reduzieren:**
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # CONF_SWAPSIZE=100
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

3. **Unnötige Services deaktivieren:**
   ```bash
   sudo systemctl disable bluetooth
   sudo systemctl disable avahi-daemon
   sudo systemctl disable triggerhappy
   ```

4. **Lightweight Theme verwenden:**
   - In App: Einstellungen → Appearance → Theme: "Dark" oder "Light"

#### Problem: Chromium sehr langsam
**Lösung:**
```bash
# Hardware-Beschleunigung in Chromium:
# Erstelle ~/.config/chromium-flags.conf
mkdir -p ~/.config
cat > ~/.config/chromium-flags.conf <<EOF
--enable-features=VaapiVideoDecoder
--disable-features=UseChromeOSDirectVideoDecoder
--enable-gpu-rasterization
--ignore-gpu-blocklist
EOF
```

---

### VNC-Probleme

#### Problem: VNC-Buttons in Settings funktionieren nicht
**Diagnose:**
```bash
# Prüfe ob VNC installiert ist
systemctl status vncserver-x11-serviced

# Falls nicht gefunden:
sudo apt-cache search realvnc
```

**Installation (falls fehlt):**
```bash
# Für Raspberry Pi OS:
sudo apt-get install realvnc-vnc-server

# Für DietPi:
# dietpi-software → VNC Server auswählen
```

#### Problem: "Connection refused" bei VNC-Verbindung
**Lösung:**
```bash
# Prüfe ob Service läuft
sudo systemctl status vncserver-x11-serviced

# Starte manuell
sudo systemctl start vncserver-x11-serviced

# Port prüfen
sudo netstat -tulpn | grep 5900
```

---

### Datenbank/Config-Probleme

#### Problem: Einstellungen werden nicht gespeichert
**Diagnose:**
```bash
# Prüfe Permissions
ls -la /opt/kidlauncher/apps/week_calendar/config/

# Prüfe ob settings.json existiert
cat /opt/kidlauncher/apps/week_calendar/config/settings.json
```

**Lösung:**
```bash
# Setze Permissions
sudo chown -R dietpi:dietpi /opt/kidlauncher/apps/week_calendar/config/
sudo chmod 755 /opt/kidlauncher/apps/week_calendar/config/
sudo chmod 644 /opt/kidlauncher/apps/week_calendar/config/settings.json
```

#### Problem: Kalender-Daten verschwinden nach Reboot
**Lösung:**
```bash
# Datenbank ist in:
/opt/kidlauncher/apps/week_calendar/calendar.db

# Prüfe ob beschreibbar:
ls -la /opt/kidlauncher/apps/week_calendar/*.db

# Setze Permissions:
sudo chown dietpi:dietpi /opt/kidlauncher/apps/week_calendar/*.db
```

---

### Netzwerk/Internet

#### Problem: Wetter wird nicht geladen
**Diagnose:**
```bash
# Test Internet-Verbindung
ping -c 3 open-meteo.com

# Test API direkt
curl "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true"
```

**Lösung:**
- Prüfe WiFi/LAN Verbindung
- Firewall-Einstellungen prüfen
- DNS-Server prüfen: `cat /etc/resolv.conf`

---

## Kompletter Reset

Falls alles andere fehlschlägt:

```bash
# 1. Komplett deinstallieren
sudo bash uninstall.sh

# 2. Neustart
sudo reboot

# 3. Neu installieren
cd ~/Kinderkuchen
sudo bash install.sh
```

---

## Logs und Debug-Informationen sammeln

Für Support-Anfragen:

```bash
# System-Info
cat /proc/device-tree/model
free -h
df -h

# Service Status
sudo systemctl status kidlauncher

# Logs (letzte 100 Zeilen)
sudo journalctl -u kidlauncher -n 100 > kidlauncher.log

# Python-Fehler (manuell starten)
cd /opt/kidlauncher
source venv/bin/activate
python apps/week_calendar/main.py --windowed 2>&1 | tee debug.log
```

---

## Support

Falls diese Anleitung nicht hilft:

1. **GitHub Issues:** https://github.com/4maggio/Kinderkuchen/issues
2. **Logs mitschicken** (siehe oben)
3. **System-Info angeben:** Pi-Modell, OS-Version, Installation-Methode
