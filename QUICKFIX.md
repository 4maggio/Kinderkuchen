# Schnelle Fehlerbehebung nach Installation

## Problem: Schwarzer Bildschirm nach Reboot

Falls nach der Installation der Bildschirm schwarz bleibt:

### Lösung 1: X11 manuell starten (Temporär)
```bash
# Via SSH einloggen
ssh dietpi@raspberrypi.local

# X11 manuell starten
startx
```

### Lösung 2: .xinitrc reparieren
```bash
# Via SSH einloggen
ssh dietpi@raspberrypi.local

# .xinitrc editieren
nano ~/.xinitrc
```

Füge **am Ende** der Datei hinzu:
```bash
# Launch the Kid Launcher app
cd /opt/kidlauncher
/opt/kidlauncher/venv/bin/python /opt/kidlauncher/apps/week_calendar/main.py
```

Dann:
```bash
# Speichern: Ctrl+O, Enter, Ctrl+X
chmod +x ~/.xinitrc

# Reboot
sudo reboot
```

### Lösung 3: Direkt in .bash_profile starten
```bash
# Via SSH
ssh dietpi@raspberrypi.local

# .bash_profile editieren
nano ~/.bash_profile
```

Nach dem `startx`-Block einfügen:
```bash
# Auto-start X11 on login
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    cd /opt/kidlauncher
    xinit /opt/kidlauncher/venv/bin/python /opt/kidlauncher/apps/week_calendar/main.py -- :0
fi
```

## Problem: RealVNC funktioniert nicht

### VNC Passwort setzen:
```bash
# Via SSH
ssh dietpi@raspberrypi.local

# Passwort für VNC Service setzen
sudo vncpasswd -service

# VNC Service starten
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service

# Status prüfen
sudo systemctl status vncserver-x11-serviced.service
```

### VNC Port prüfen:
```bash
# Sollte Port 5900 lauschen
sudo netstat -tlnp | grep 5900
```

### VNC Client verbinden:
- IP-Adresse des Pi herausfinden: `hostname -I`
- VNC Viewer öffnen und verbinden: `<IP-ADRESSE>:5900`
- Passwort eingeben (das mit vncpasswd gesetzte)

## Problem: Display bleibt weiß

Wenn das Display weiß bleibt, kann das ein Problem mit dem Touchscreen-Treiber sein:

```bash
# SSH einloggen
ssh dietpi@raspberrypi.local

# Xorg Log prüfen
cat /var/log/Xorg.0.log

# Display-Rotation prüfen/setzen
sudo nano /boot/config.txt
```

Füge hinzu (falls nicht vorhanden):
```
display_rotate=0
gpu_mem=128
```

Für 180° Rotation (Touchscreen upside down):
```
display_rotate=2
```

## Logs prüfen

```bash
# X11 Log
cat ~/.local/share/xorg/Xorg.0.log

# Systemd journal für kidlauncher
sudo journalctl -u kidlauncher -n 50

# Python-Fehler (falls die App startet)
cd /opt/kidlauncher
./venv/bin/python apps/week_calendar/main.py
```

## Komplett neu installieren

Falls nichts hilft:
```bash
# Alte Installation entfernen
cd /opt/kidlauncher
sudo bash uninstall.sh

# Neu installieren
sudo bash install.sh
```

---

Bei weiteren Problemen siehe [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
