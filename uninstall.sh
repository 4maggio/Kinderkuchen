#!/bin/bash
###############################################################################
# RaspiGui Kid Launcher - Uninstall Script
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/kidlauncher"

print_header() {
    echo -e "\n${YELLOW}$1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

ask_yes_no() {
    local prompt="$1"
    while true; do
        read -p "$prompt [y/N]: " yn
        yn=${yn:-n}
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Bitte mit 'y' oder 'n' antworten.";;
        esac
    done
}

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Dieses Skript muss als root ausgeführt werden.${NC}"
    echo "Verwende: sudo bash uninstall.sh"
    exit 1
fi

print_header "RaspiGui Kid Launcher Deinstallation"

echo "Diese Aktion wird folgendes entfernen:"
echo "  • Systemd Service"
echo "  • Installation in $INSTALL_DIR"
echo "  • Auto-Login Konfiguration"
echo ""

if ! ask_yes_no "Wirklich deinstallieren?"; then
    echo "Abgebrochen."
    exit 0
fi

# Stop and disable service
if systemctl is-active --quiet kidlauncher; then
    systemctl stop kidlauncher
    print_success "Service gestoppt"
fi

if systemctl is-enabled --quiet kidlauncher 2>/dev/null; then
    systemctl disable kidlauncher
    print_success "Service deaktiviert"
fi

# Remove service file
if [ -f /etc/systemd/system/kidlauncher.service ]; then
    rm /etc/systemd/system/kidlauncher.service
    systemctl daemon-reload
    print_success "Service-Datei entfernt"
fi

# Remove auto-login
if [ -f /etc/systemd/system/getty@tty1.service.d/autologin.conf ]; then
    if ask_yes_no "Auto-Login entfernen?"; then
        rm /etc/systemd/system/getty@tty1.service.d/autologin.conf
        print_success "Auto-Login entfernt"
    fi
fi

# Remove installation
if [ -d "$INSTALL_DIR" ]; then
    if ask_yes_no "Installation ($INSTALL_DIR) löschen?"; then
        rm -rf "$INSTALL_DIR"
        print_success "Installation entfernt"
    fi
fi

# Ask about packages
echo ""
if ask_yes_no "Installierte Pakete entfernen? (X11, Chromium, etc.)"; then
    apt-get remove --purge -y \
        chromium-browser \
        openbox \
        xserver-xorg-core \
        unclutter
    
    apt-get autoremove -y
    print_success "Pakete entfernt"
fi

echo ""
echo -e "${GREEN}Deinstallation abgeschlossen!${NC}"
echo ""
echo "Hinweis: Python3 und grundlegende Pakete wurden nicht entfernt,"
echo "da sie möglicherweise von anderen Programmen benötigt werden."
