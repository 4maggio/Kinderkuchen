#!/bin/bash
###############################################################################
# RaspiGui Kid Launcher - DietPi Installation Script
# 
# Installiert alle Abhängigkeiten minimal und konfiguriert Auto-Boot
# Optimiert für Raspberry Pi 2 mit 7" Touchscreen (800x480)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/kidlauncher"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_USER="dietpi"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

select_service_user() {
    print_header "Benutzerkonto auswählen"

    local selected_user="$SERVICE_USER"
    if [ "$AUTO_YES" != "true" ]; then
        read -p "Launcher unter welchem Benutzer starten? [$SERVICE_USER]: " input_user
        input_user=${input_user:-$SERVICE_USER}
        selected_user="$input_user"
    else
        echo "Auto-Installation aktiv - verwende Benutzer '$SERVICE_USER'"
    fi

    if ! id -u "$selected_user" >/dev/null 2>&1; then
        print_warning "Benutzer '$selected_user' existiert nicht."
        if ask_yes_no "Benutzer '$selected_user' jetzt anlegen?" "y"; then
            adduser --disabled-password --gecos "" "$selected_user"
            print_success "Benutzer '$selected_user' angelegt"
        else
            print_error "Benutzer wird benötigt - Installation abgebrochen."
            exit 1
        fi
    fi

    SERVICE_USER="$selected_user"
    print_success "Verwende Benutzer '$SERVICE_USER'"
    ensure_service_user_groups
}

ensure_service_user_groups() {
    local groups=(tty video input)
    for group in "${groups[@]}"; do
        if id -nG "$SERVICE_USER" | grep -qw "$group"; then
            echo "  ✓ $SERVICE_USER ist bereits in Gruppe $group"
        else
            usermod -aG "$group" "$SERVICE_USER"
            print_success "$SERVICE_USER zu Gruppe $group hinzugefügt"
        fi
    done
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    
    # Auto-yes mode (full installation)
    if [ "$AUTO_YES" = "true" ]; then
        echo "$prompt [AUTO: yes]"
        return 0
    fi
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    while true; do
        read -p "$prompt" yn
        yn=${yn:-$default}
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Bitte mit 'y' oder 'n' antworten.";;
        esac
    done
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Dieses Skript muss als root ausgeführt werden."
        echo "Bitte verwende: sudo bash install.sh"
        exit 1
    fi
}

check_dietpi() {
    if [ ! -f /boot/dietpi/.version ]; then
        print_warning "DietPi wurde nicht erkannt. Installation fortsetzen?"
        if ! ask_yes_no "Fortfahren"; then
            exit 1
        fi
    else
        print_success "DietPi erkannt"
    fi
}

###############################################################################
# System Update
###############################################################################

update_system() {
    print_header "System Update"
    
    if ask_yes_no "System-Pakete aktualisieren?" "y"; then
        # Clean apt cache to avoid download issues
        apt-get clean
        
        # Configure apt for better reliability
        cat > /etc/apt/apt.conf.d/99-dietpi-custom <<EOF
Acquire::Retries "3";
Acquire::http::Timeout "60";
Acquire::https::Timeout "60";
Acquire::Queue-Mode "host";
EOF
        
        print_success "APT konfiguriert (Retries, Timeouts)"
        
        # Update with retries
        local retry=0
        local max_retries=3
        while [ $retry -lt $max_retries ]; do
            if apt-get update; then
                break
            fi
            retry=$((retry + 1))
            if [ $retry -lt $max_retries ]; then
                print_warning "apt-get update fehlgeschlagen, Versuch $retry/$max_retries..."
                sleep 5
            else
                print_error "apt-get update nach $max_retries Versuchen fehlgeschlagen"
                return 1
            fi
        done
        
        apt-get upgrade -y
        print_success "System aktualisiert"
    else
        print_warning "System-Update übersprungen"
        # Still do a minimal update for package lists
        apt-get update || print_warning "apt-get update fehlgeschlagen (fortfahren...)"
    fi
}

###############################################################################
# DietPi Optimizations
###############################################################################

optimize_dietpi() {
    # Only run if DietPi is detected
    if [ ! -f /boot/dietpi/.version ]; then
        return
    fi
    
    print_header "DietPi Optimierungen"
    
    if ! ask_yes_no "DietPi für minimalen Ressourcen-Verbrauch optimieren?" "y"; then
        return
    fi
    
    # Disable unnecessary services for kiosk mode
    echo "Deaktiviere unnötige Services..."
    
    # Services that are not needed for kiosk
    SERVICES_TO_DISABLE=(
        "bluetooth"
        "avahi-daemon"
        "triggerhappy"
        "cron"
    )
    
    for service in "${SERVICES_TO_DISABLE[@]}"; do
        if systemctl is-enabled "$service" &>/dev/null; then
            systemctl disable "$service" 2>/dev/null || true
            systemctl stop "$service" 2>/dev/null || true
            echo "  ✓ $service deaktiviert"
        fi
    done
    
    # Reduce logging to save I/O
    if [ -f /etc/systemd/journald.conf ]; then
        sed -i 's/^#Storage=.*/Storage=volatile/' /etc/systemd/journald.conf
        sed -i 's/^#RuntimeMaxUse=.*/RuntimeMaxUse=20M/' /etc/systemd/journald.conf
        echo "  ✓ Logging optimiert (volatile, max 20MB)"
    fi
    
    # Hardware optimizations
    CONFIG_FILE="/boot/config.txt"
    if [ -f "$CONFIG_FILE" ]; then
        echo ""
        echo "Hardware-Optimierungen (für 7\" Touchscreen):"
        
        # Disable HDMI if using touchscreen
        if ask_yes_no "HDMI deaktivieren? (empfohlen bei 7\" Touchscreen)" "y"; then
            sed -i '/^hdmi_blanking=/d' "$CONFIG_FILE"
            sed -i '/^hdmi_force_hotplug=/d' "$CONFIG_FILE"
            echo "hdmi_blanking=2" >> "$CONFIG_FILE"
            echo "hdmi_force_hotplug=0" >> "$CONFIG_FILE"
            echo "  ✓ HDMI deaktiviert (spart ~5-10MB RAM)"
        fi
        
        # Optional: Disable WiFi (only if ethernet available)
        echo ""
        echo "⚠️  ACHTUNG: WiFi nur deaktivieren wenn Ethernet verwendet wird!"
        if ask_yes_no "WiFi deaktivieren? (nur bei Ethernet-Verbindung)" "n"; then
            sed -i '/^dtoverlay=disable-wifi/d' "$CONFIG_FILE"
            echo "dtoverlay=disable-wifi" >> "$CONFIG_FILE"
            echo "  ✓ WiFi deaktiviert (spart ~10-15MB RAM)"
        fi
    fi
    
    print_success "DietPi optimiert - spart bis zu ~55MB RAM"
}

###############################################################################
# Safe APT Install Helper
###############################################################################

safe_apt_install() {
    local packages="$@"
    local retry=0
    local max_retries=2
    
    while [ $retry -le $max_retries ]; do
        if apt-get install -y --no-install-recommends $packages; then
            return 0
        fi
        
        retry=$((retry + 1))
        if [ $retry -le $max_retries ]; then
            print_warning "Installation fehlgeschlagen, Versuch $retry/$max_retries..."
            apt-get clean
            apt-get update -qq || true
            sleep 3
        else
            print_error "Installation nach $max_retries Versuchen fehlgeschlagen: $packages"
            return 1
        fi
    done
}

###############################################################################
# Install Minimal X11 and Openbox
###############################################################################

install_x11() {
    print_header "X11 und Openbox Installation"
    
    echo "Chromium benötigt X11. Wir installieren eine minimale X11-Umgebung."
    echo "Geschätzter Speicherbedarf: ~80MB"
    
    if ! ask_yes_no "X11 und Openbox installieren?" "y"; then
        print_warning "X11 übersprungen - Chromium wird nicht funktionieren!"
        return
    fi
    
    # Minimal X11 packages (absolute minimum)
    safe_apt_install xserver-xorg-core xserver-xorg-video-fbdev xinit openbox unclutter
    
    print_success "X11 und Openbox installiert"
}

###############################################################################
# Install Python and Dependencies
###############################################################################

install_python() {
    print_header "Python 3 Installation"
    
    # Install Python 3 and venv (minimal)
    safe_apt_install python3 python3-venv python3-dev
    
    # Git is optional - only install if user wants updates via git
    if ask_yes_no "Git installieren? (für Updates via git pull)" "n"; then
        safe_apt_install git
        print_success "Git installiert"
    else
        print_warning "Git übersprungen - Updates nur manuell möglich"
    fi
    
    print_success "Python 3 installiert"
}

install_pyqt5() {
    print_header "PyQt5 Installation"
    
    echo "PyQt5 kann entweder als System-Paket oder via pip installiert werden."
    echo "System-Paket: Schneller, kleiner (~25MB)"
    echo "pip: Aktueller, aber größer (~80MB)"
    
    if ask_yes_no "System-Paket verwenden? (empfohlen)" "y"; then
        # Only install base PyQt5 package (includes QtWidgets)
        safe_apt_install python3-pyqt5
        
        print_success "PyQt5 als System-Paket installiert"
        return 0
    else
        print_warning "PyQt5 wird später via pip im venv installiert"
        return 1
    fi
}

###############################################################################
# Install Chromium
###############################################################################

install_chromium() {
    print_header "Chromium Browser Installation"
    
    echo "Chromium wird für Website-Apps im Kiosk-Modus benötigt."
    echo "Geschätzter Speicherbedarf: ~200MB"
    
    if ! ask_yes_no "Chromium installieren?" "y"; then
        print_warning "Chromium übersprungen - Website-Apps funktionieren nicht!"
        return
    fi
    
    safe_apt_install chromium
    
    print_success "Chromium installiert"
}

###############################################################################
# Install RealVNC Server
###############################################################################

install_vnc() {
    print_header "RealVNC Server Installation"
    
    echo "RealVNC ermöglicht Fernzugriff auf den Raspberry Pi."
    echo "Geschätzter Speicherbedarf: ~20MB"
    
    if ! ask_yes_no "RealVNC installieren?" "y"; then
        print_warning "RealVNC übersprungen"
        return
    fi
    
    # Check if RealVNC is available in repositories
    if apt-cache show realvnc-vnc-server &>/dev/null; then
        safe_apt_install realvnc-vnc-server
        
        # Enable VNC service
        systemctl enable vncserver-x11-serviced.service
        systemctl start vncserver-x11-serviced.service 2>/dev/null || true
        
        print_success "RealVNC Server installiert und aktiviert"
        echo ""
        echo "⚠️  WICHTIG: VNC-Passwort muss noch gesetzt werden:"
        echo "    sudo vncpasswd -service"
        echo "    (wird in den Eltern-Einstellungen auch konfigurierbar sein)"
    else
        print_warning "RealVNC nicht in Repositories gefunden"
        echo "Für Raspberry Pi OS kann RealVNC manuell installiert werden:"
        echo "https://www.realvnc.com/download/file/vnc.files/VNC-Server-7.x.x-Linux-ARM.deb"
    fi
}

###############################################################################
# Install On-Screen Keyboard
###############################################################################

install_onscreen_keyboard() {
    print_header "On-Screen Keyboard Installation"
    
    echo "Touchscreen-Tastatur für Texteingabe ohne physische Tastatur."
    echo "Geschätzter Speicherbedarf: ~5MB"
    
    if ! ask_yes_no "On-Screen Keyboard (matchbox-keyboard) installieren?" "y"; then
        print_warning "On-Screen Keyboard übersprungen"
        return
    fi
    
    safe_apt_install matchbox-keyboard
    
    print_success "On-Screen Keyboard installiert"
}

###############################################################################
# Setup Project
###############################################################################

setup_project() {
    print_header "Projekt Setup"
    
    # Get current script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    echo "Aktuelles Verzeichnis: $SCRIPT_DIR"
    echo "Installations-Ziel: $INSTALL_DIR"
    
    if [ "$SCRIPT_DIR" = "$INSTALL_DIR" ]; then
        print_success "Bereits im Installations-Verzeichnis"
    else
        if ask_yes_no "Projekt nach $INSTALL_DIR kopieren?" "y"; then
            mkdir -p "$INSTALL_DIR"
            cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
            cd "$INSTALL_DIR"
            print_success "Projekt kopiert"
        else
            INSTALL_DIR="$SCRIPT_DIR"
            print_warning "Installation im aktuellen Verzeichnis: $INSTALL_DIR"
        fi
    fi
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
}

setup_venv() {
    print_header "Python Virtual Environment Setup"
    
    cd "$INSTALL_DIR"
    
    # Determine if we should use system-site-packages (for system PyQt5)
    local venv_args=""
    if [ "$PYQT_SYSTEM" = "0" ]; then
        # Return 0 = System package was installed
        venv_args="--system-site-packages"
        print_success "venv wird mit Zugriff auf System-Pakete erstellt (für PyQt5)..."
    fi
    
    # Create venv
    if [ ! -d "$VENV_DIR" ]; then
        print_success "Erstelle Virtual Environment..."
        sudo -u $SERVICE_USER python3 -m venv $venv_args "$VENV_DIR"
        print_success "venv erstellt"
    else
        print_success "venv existiert bereits"
    fi
    
    # Upgrade pip
    sudo -u $SERVICE_USER "$VENV_DIR/bin/pip" install --upgrade pip
    
    # Install Python packages
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        print_success "Installiere Python-Pakete..."
        
        if [ "$PYQT_SYSTEM" = "0" ]; then
            # Skip PyQt5 from requirements.txt if using system package
            print_success "PyQt5 wird übersprungen (System-Paket wird verwendet)..."
            grep -v "^PyQt5" "$INSTALL_DIR/requirements.txt" > "$INSTALL_DIR/requirements_temp.txt"
            sudo -u $SERVICE_USER "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements_temp.txt"
            rm "$INSTALL_DIR/requirements_temp.txt"
        else
            # Install all packages including PyQt5
            sudo -u $SERVICE_USER "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
        fi
        
        print_success "Python-Pakete installiert"
    else
        print_warning "requirements.txt nicht gefunden - übersprungen"
    fi
}

###############################################################################
# Configure Display and Touch
###############################################################################

configure_display() {
    print_header "Display & Touchscreen Konfiguration"
    
    echo "Raspberry Pi 7\" Touchscreen (offiziell) Konfiguration"
    echo ""
    
    if ! ask_yes_no "Touchscreen konfigurieren?" "y"; then
        return
    fi
    
    CONFIG_FILE="/boot/config.txt"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "$CONFIG_FILE nicht gefunden"
        return
    fi
    
    # Enable official 7" touchscreen overlay
    print_header "Touchscreen Treiber aktivieren"
    
    # Remove old touchscreen configs
    sed -i '/^dtoverlay=rpi-ft5406/d' "$CONFIG_FILE"
    sed -i '/^dtoverlay=vc4-kms-v3d/d' "$CONFIG_FILE"
    sed -i '/^dtoverlay=vc4-fkms-v3d/d' "$CONFIG_FILE"
    
    # Add touchscreen overlay (for official 7" display)
    if ! grep -q "dtoverlay=rpi-ft5406" "$CONFIG_FILE"; then
        echo "dtoverlay=rpi-ft5406" >> "$CONFIG_FILE"
        print_success "Touchscreen Overlay aktiviert"
    fi
    
    # Use fake KMS for better compatibility with Pi 2
    if ! grep -q "dtoverlay=vc4-fkms-v3d" "$CONFIG_FILE"; then
        echo "dtoverlay=vc4-fkms-v3d" >> "$CONFIG_FILE"
        print_success "Video Treiber konfiguriert (vc4-fkms-v3d für Pi2)"
    fi
    
    # Ask for rotation
    echo ""
    echo "Display-Rotation auswählen:"
    echo "0 = Normal (0°)"
    echo "1 = 90° im Uhrzeigersinn"
    echo "2 = 180° (auf dem Kopf)"
    echo "3 = 270° im Uhrzeigersinn"
    read -p "Rotation [0-3]: " rotation
    rotation=${rotation:-0}
    
    # Remove old display_rotate settings
    sed -i '/^display_rotate=/d' "$CONFIG_FILE"
    sed -i '/^lcd_rotate=/d' "$CONFIG_FILE"
    
    # Add new rotation
    if [ "$rotation" != "0" ]; then
        echo "display_rotate=$rotation" >> "$CONFIG_FILE"
        echo "lcd_rotate=$rotation" >> "$CONFIG_FILE"
        print_success "Display-Rotation auf $rotation gesetzt"
    fi
    
    # Ensure touchscreen input driver is available
    if ! dpkg -l | grep -q xserver-xorg-input-evdev; then
        print_header "Touchscreen Input-Treiber installieren"
        safe_apt_install xserver-xorg-input-evdev
        print_success "Input-Treiber installiert"
    fi
    
    print_success "Touchscreen konfiguriert - Neustart erforderlich"
}

###############################################################################
# Configure Audio Output
###############################################################################

configure_audio() {
    print_header "Audio Konfiguration"

    if ! ask_yes_no "Onboard-Klinke als Standardausgabe setzen?" "y"; then
        print_warning "Audio-Konfiguration übersprungen"
        return
    fi

    CONFIG_FILE="/boot/config.txt"
    if [ -f "$CONFIG_FILE" ]; then
        sed -i '/^dtparam=audio=/d' "$CONFIG_FILE"
        echo "dtparam=audio=on" >> "$CONFIG_FILE"
        print_success "Analog-Audio im config.txt aktiviert"
    else
        print_warning "$CONFIG_FILE nicht gefunden - Überspringe dtparam"
    fi

    # Ensure ALSA tools are present for mixer configuration
    if ! command -v amixer >/dev/null 2>&1; then
        safe_apt_install alsa-utils || print_warning "alsa-utils konnte nicht installiert werden"
    fi

    if command -v amixer >/dev/null 2>&1; then
        amixer cset numid=3 1 >/dev/null 2>&1 || print_warning "Konnte Audio-Ausgabe nicht auf Kopfhörer setzen"
        amixer set PCM 90% >/dev/null 2>&1 || true
    fi

    cat > /etc/asound.conf <<'EOF'
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
EOF

    print_success "ALSA-Standardausgabe auf Headphone Port gesetzt"
}

###############################################################################
# Configure Auto-Boot
###############################################################################

configure_autoboot() {
    print_header "Auto-Boot Konfiguration"
    
    echo "Soll die App beim Systemstart automatisch starten?"
    if ! ask_yes_no "Auto-Boot aktivieren?" "y"; then
        print_warning "Auto-Boot übersprungen"
        return
    fi

    ensure_service_user_groups
    
    # Create systemd service (as backup/monitoring - primary launch via .xinitrc)
    cat > /etc/systemd/system/kidlauncher.service <<EOF
[Unit]
Description=Kid Launcher GUI (Monitor)
After=graphical.target

[Service]
Type=oneshot
User=$SERVICE_USER
RemainAfterExit=yes
ExecStart=/bin/true

[Install]
WantedBy=graphical.target
EOF
    
    print_success "Systemd Service erstellt"
    
    # Create X11 auto-start script
    mkdir -p /home/$SERVICE_USER
    cat > /home/$SERVICE_USER/.xinitrc <<EOF
#!/bin/bash
# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 0.1 &

# Start Openbox in background
openbox &

# Wait a moment for Openbox to start
sleep 2

# Launch the Kid Launcher app
cd "$INSTALL_DIR"
"$VENV_DIR/bin/python" "$INSTALL_DIR/apps/week_calendar/main.py"
EOF
    
    chmod +x /home/$SERVICE_USER/.xinitrc
    chown $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.xinitrc
    
    print_success ".xinitrc erstellt"
    
    # Configure auto-login with X11
    mkdir -p /etc/systemd/system/getty@tty1.service.d/
    cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $SERVICE_USER --noclear %I \$TERM
EOF
    
    # Add startx to .bash_profile
    if ! grep -q "startx" /home/$SERVICE_USER/.bash_profile 2>/dev/null; then
        cat >> /home/$SERVICE_USER/.bash_profile <<EOF

# Auto-start X11 on login
if [ -z "\$DISPLAY" ] && [ "\$(tty)" = "/dev/tty1" ]; then
    startx
fi
EOF
        chown $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.bash_profile
        print_success "Auto-startx konfiguriert"
    fi
    
    # Enable service
    systemctl enable kidlauncher.service
    systemctl daemon-reload
    
    print_success "Auto-Boot aktiviert"
}

###############################################################################
# Create Launch Script
###############################################################################

create_launch_script() {
    print_header "Launch-Skript erstellen"
    
    cat > "$INSTALL_DIR/start.sh" <<EOF
#!/bin/bash
# RaspiGui Kid Launcher Start Script

cd "$INSTALL_DIR"
source "$VENV_DIR/bin/activate"
python apps/week_calendar/main.py "\$@"
EOF
    
    chmod +x "$INSTALL_DIR/start.sh"
    chown $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR/start.sh"
    
    print_success "start.sh erstellt"
}

###############################################################################
# Final Configuration
###############################################################################

final_setup() {
    print_header "Abschluss-Konfiguration"
    
    # Create config directory
    mkdir -p "$INSTALL_DIR/apps/week_calendar/config"
    chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR/apps/week_calendar/config"
    
    # Memory optimization for Pi 2
    echo "Speicher-Optimierung für Raspberry Pi 2"
    if ask_yes_no "GPU-Speicher auf 128MB setzen? (empfohlen)" "y"; then
        CONFIG_FILE="/boot/config.txt"
        if [ -f "$CONFIG_FILE" ]; then
            sed -i '/^gpu_mem=/d' "$CONFIG_FILE"
            echo "gpu_mem=128" >> "$CONFIG_FILE"
            print_success "GPU-Speicher konfiguriert"
        fi
    fi
    
    print_success "Konfiguration abgeschlossen"
}

###############################################################################
# Summary and Instructions
###############################################################################

print_summary() {
    print_header "Installation Abgeschlossen!"
    
    echo -e "${GREEN}✓ Installation erfolgreich${NC}\n"
    
    echo "Installationsverzeichnis: $INSTALL_DIR"
    echo "Virtual Environment: $VENV_DIR"
    echo ""
    
    echo -e "${BLUE}Manuelle Befehle:${NC}"
    echo "  Starten:  cd $INSTALL_DIR && ./start.sh"
    echo "  Windowed: cd $INSTALL_DIR && ./start.sh --windowed"
    echo "  Service:  sudo systemctl start kidlauncher"
    echo "  Status:   sudo systemctl status kidlauncher"
    echo ""
    
    echo -e "${YELLOW}Wichtige Hinweise:${NC}"
    echo "  • Die App startet beim nächsten Neustart automatisch"
    echo "  • Eltern-Einstellungen: ⚙-Button in der App (Standard-PIN: 1234)"
    echo "  • Logs: journalctl -u kidlauncher -f"
    echo ""
    
    if ask_yes_no "Jetzt neu starten?" "n"; then
        echo "System wird neu gestartet..."
        reboot
    else
        echo -e "\n${GREEN}Installation abgeschlossen. Bitte manuell neu starten.${NC}"
    fi
}

###############################################################################
# Main Installation Flow
###############################################################################

main() {
    clear
    
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     RaspiGui Kid Launcher - Installation                 ║
║     Optimiert für Raspberry Pi 2 + 7" Touchscreen        ║
║     Lizenz: AGPL-3.0                                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
    
    echo ""
    echo "Dieses Skript installiert alle Abhängigkeiten und konfiguriert"
    echo "das System für automatischen Start beim Booten."
    echo ""
    echo "Speicherbedarf (mit --no-install-recommends optimiert):"
    echo "  - Minimal (ohne Chromium/VNC): ~100MB"
    echo "  - Empfohlen (mit Chromium/VNC/Keyboard): ~450MB"
    echo "  - Jedes Paket kann einzeln aktiviert/deaktiviert werden"
    echo ""
    echo "Geschätzte Installationszeit: 10-30 Minuten"
    echo ""
    echo "Installation starten? [y/n/full]"
    echo "  y    = Interaktiv (mit Rückfragen)"
    echo "  n    = Abbrechen"
    echo "  full = Automatisch ALLE Pakete installieren (keine Rückfragen)"
    echo ""
    read -p "Deine Wahl [y]: " install_choice
    install_choice=${install_choice:-y}
    
    case $install_choice in
        [Yy]* )
            AUTO_YES="false"
            ;;
        [Nn]* )
            print_warning "Installation abgebrochen"
            exit 0
            ;;
        [Ff]* | full | FULL )
            AUTO_YES="true"
            print_success "Full-Installation aktiviert - alle Pakete werden automatisch installiert"
            sleep 1
            ;;
        * )
            print_error "Ungültige Eingabe. Bitte 'y', 'n' oder 'full' eingeben."
            exit 1
            ;;
    esac
    
    # Run installation steps
    check_root
    check_dietpi
    select_service_user
    update_system
    optimize_dietpi
    install_python
    install_x11
    install_pyqt5
    PYQT_SYSTEM=$?  # Store return value: 0 = system package, 1 = pip
    install_chromium
    install_vnc
    install_onscreen_keyboard
    setup_project
    setup_venv
    configure_display
    configure_audio
    configure_autoboot
    create_launch_script
    final_setup
    print_summary
}

# Run main installation
main "$@"
