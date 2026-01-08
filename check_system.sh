#!/bin/bash
# Quick Test Script - Run before full installation
# Tests if basic dependencies are available

echo "=== RaspiGui Pre-Installation Check ==="
echo ""

check_command() {
    if command -v $1 &> /dev/null; then
        echo "✓ $1 found"
        return 0
    else
        echo "✗ $1 NOT found"
        return 1
    fi
}

# Check Python
if check_command python3; then
    python3 --version
fi

# Check pip
check_command pip3

# Check git
check_command git

# Check if running on Pi
if [ -f /proc/device-tree/model ]; then
    echo ""
    echo "Device: $(cat /proc/device-tree/model)"
fi

# Check available memory
if command -v free &> /dev/null; then
    echo ""
    echo "Memory:"
    free -h | grep Mem
fi

# Check available disk space
if command -v df &> /dev/null; then
    echo ""
    echo "Disk Space:"
    df -h / | tail -1
fi

echo ""
echo "=== Check Complete ==="
echo ""
echo "If all basic tools are present, you can run:"
echo "  sudo bash install.sh"
