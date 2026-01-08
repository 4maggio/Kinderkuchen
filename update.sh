#!/bin/bash
###############################################################################
# RaspiGui Kid Launcher - Update Script
# Aktualisiert die Installation auf die neueste Version
###############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL_DIR="/opt/kidlauncher"
BACKUP_DIR="/opt/kidlauncher_backup_$(date +%Y%m%d_%H%M%S)"
SERVICE_USER="dietpi"

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    
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

if [ "$EUID" -ne 0 ]; then 
    print_error "Dieses Skript muss als root ausgeführt werden."
    echo "Verwende: sudo bash update.sh"
    exit 1
fi

cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     RaspiGui Kid Launcher - Update                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF

echo ""
echo "Dieses Skript aktualisiert die RaspiGui Installation."
echo ""

if [ ! -d "$INSTALL_DIR" ]; then
    print_error "Installation nicht gefunden in: $INSTALL_DIR"
    echo "Bitte zuerst mit install.sh installieren."
    exit 1
fi

# Check if git repo
cd "$INSTALL_DIR"
if [ ! -d ".git" ]; then
    print_warning "Keine Git-Repository gefunden."
    echo "Manuelle Installation erkannt."
    echo ""
    echo "Für Updates:"
    echo "1. Neue Version herunterladen"
    echo "2. Backup erstellen: cp -r $INSTALL_DIR $BACKUP_DIR"
    echo "3. Neue Dateien kopieren"
    echo "4. Service neustarten: sudo systemctl restart kidlauncher"
    exit 1
fi

echo "Aktuelle Version:"
git log -1 --oneline
echo ""

# Stop service
if systemctl is-active --quiet kidlauncher; then
    echo "Stoppe Service..."
    systemctl stop kidlauncher
    print_success "Service gestoppt"
fi

# Create backup
if ask_yes_no "Backup erstellen?" "y"; then
    echo "Erstelle Backup nach: $BACKUP_DIR"
    
    # Backup config and database
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "$INSTALL_DIR/apps/week_calendar/config" ]; then
        cp -r "$INSTALL_DIR/apps/week_calendar/config" "$BACKUP_DIR/"
        print_success "Config gesichert"
    fi
    
    if [ -f "$INSTALL_DIR/apps/week_calendar/calendar.db" ]; then
        cp "$INSTALL_DIR/apps/week_calendar/calendar.db" "$BACKUP_DIR/"
        print_success "Datenbank gesichert"
    fi
fi

# Pull updates
echo "Hole Updates..."
git fetch origin
git pull origin main

print_success "Code aktualisiert"

# Update Python dependencies
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    if ask_yes_no "Python-Pakete aktualisieren?" "y"; then
        echo "Aktualisiere Python-Pakete..."
        sudo -u $SERVICE_USER "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
        sudo -u $SERVICE_USER "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --upgrade
        print_success "Python-Pakete aktualisiert"
    fi
fi

# Restore config if it was overwritten
if [ -d "$BACKUP_DIR/config" ]; then
    if ask_yes_no "Backup-Config wiederherstellen?" "y"; then
        cp -r "$BACKUP_DIR/config/"* "$INSTALL_DIR/apps/week_calendar/config/" 2>/dev/null || true
        print_success "Config wiederhergestellt"
    fi
fi

# Fix permissions
chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
print_success "Permissions gesetzt"

# Restart service
if ask_yes_no "Service neu starten?" "y"; then
    systemctl start kidlauncher
    sleep 2
    
    if systemctl is-active --quiet kidlauncher; then
        print_success "Service läuft"
    else
        print_error "Service konnte nicht gestartet werden"
        echo "Prüfe Logs mit: sudo journalctl -u kidlauncher -n 50"
    fi
fi

echo ""
echo -e "${GREEN}Update abgeschlossen!${NC}"
echo ""
echo "Neue Version:"
git log -1 --oneline
echo ""
echo "Backup gespeichert in: $BACKUP_DIR"
echo ""
echo "Nützliche Befehle:"
echo "  Status:  sudo systemctl status kidlauncher"
echo "  Logs:    sudo journalctl -u kidlauncher -f"
echo "  Backup:  ls -la $BACKUP_DIR"
