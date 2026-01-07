# Copilot Instructions: RaspiGui Kid Launcher

## Project Overview
This is a kid-friendly, icon-based launcher for Raspberry Pi 2 with 7" touchscreen (800x480). The launcher provides a simple touch interface to launch apps like Chromium in kiosk mode and custom Python applications. Built for resource-constrained hardware (Pi2: 900MHz quad-core, 1GB RAM).

## Architecture

**Tech Stack:** Python 3 + PyQt5 on X11/Openbox over DietPi
- **GUI:** PyQt5 (hardware-accelerated, touch-enabled, fullscreen)
- **Process Management:** subprocess module for launching apps
- **Config:** JSON-based app definitions in `config.json`
- **Structure:** `/opt/kidlauncher/` on target Pi

**Key Design Decisions:**
- Minimal X11 setup (Openbox WM) - required for Chromium, ~10MB RAM overhead
- Single Python codebase for both launcher and custom apps
- Fullscreen PyQt5 replaces traditional desktop environment
- Apps launched as child processes; launcher monitors and awaits return

## Critical Conventions

### Performance Requirements (Pi2 Hardware Constraints)
- **Memory:** Keep total launcher footprint under 50MB
- **Startup:** Target <5 seconds from X11 start to launcher display
- **Touch Response:** Handle touch events within 100ms
- **Assets:** Icons should be 128x128 PNG, optimized/compressed

### Code Style
- Use Python 3.7+ features (DietPi default)
- Type hints for all function signatures
- Keep PyQt5 imports minimal - only import needed widgets
- Avoid heavy dependencies - stdlib preferred where possible

### File Structure Pattern
```
/opt/kidlauncher/
├── launcher.py           # Main entry point, PyQt5 GUI
├── config.json          # App definitions (editable by user)
├── apps/                # Custom Python apps (self-contained)
├── icons/               # PNG icons, 128x128, compressed
└── utils/               # Reusable modules (process, config)
```

### Configuration Schema
Apps defined in `config.json` follow this pattern:
```json
{
  "apps": [
    {
      "id": "unique_id",
      "name": "Display Name",
      "icon": "icons/filename.png",
      "command": "full command with args"
    }
  ]
}
```

## Key Workflows

### Running Locally (Development)
```bash
# Install PyQt5 on dev machine
pip install PyQt5

# Run launcher in windowed mode (800x480)
python launcher.py --windowed

# Test with mock config
python launcher.py --config test_config.json
```

### Deploying to Pi
```bash
# SSH to Pi
ssh dietpi@raspberrypi.local

# Install dependencies
sudo apt-get install python3-pyqt5 chromium-browser

# Copy files to /opt/kidlauncher/
sudo cp -r . /opt/kidlauncher/

# Configure auto-start (systemd or .xinitrc)
# See Raspi_Concept for boot integration details
```

### Adding New Apps
1. Add icon to `icons/` directory (128x128 PNG)
2. Add app definition to `config.json` under `apps` array
3. For Python apps: create module in `apps/` directory
4. Restart launcher to reload config

### Testing on Pi Hardware
- Use `htop` to monitor memory usage (keep launcher <50MB)
- Check X11 touch events: `xinput test <device_id>`
- Profile startup: add timing prints in launcher.py
- Test app switching: launch → exit → launch cycle

## Common Patterns

### Launching External Apps (Chromium Example)
```python
import subprocess
cmd = [
    "chromium-browser",
    "--kiosk",
    "--noerrdialogs", 
    "--disable-infobars",
    "https://example.com"
]
process = subprocess.Popen(cmd)
process.wait()  # Block until app exits
```

### PyQt5 Touch-Friendly Buttons
```python
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize

btn = QPushButton()
btn.setIconSize(QSize(128, 128))  # Large touch target
btn.setFixedSize(180, 180)        # 128px icon + padding
btn.clicked.connect(lambda: launch_app("app_id"))
```

### Config Loading Pattern
```python
import json
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path) as f:
        return json.load(f)
```

## Important Constraints

1. **No Deletion in Raspi_Concept:** When updating the concept file, comment out old sections with `# [DEPRECATED]` rather than deleting. Manual cleanup comes later.

2. **Resource Budget:** Pi2 has only 1GB RAM shared with GPU
   - Chromium alone can use 200-300MB
   - Leave headroom for GPU (64-128MB)
   - Launcher must be lean

3. **Touch Calibration:** Official 7" screen is rotated in some setups
   - May need `display_rotate=2` in `/boot/config.txt`
   - Touch coords must match display orientation

4. **Boot Time Critical:** Kids have low patience
   - Disable unnecessary systemd services
   - Use `systemd-analyze blame` to find bottlenecks
   - Consider splash screen during boot

## External Dependencies

- **PyQt5:** Core GUI framework (python3-pyqt5 package on Debian/DietPi)
- **Chromium:** For kiosk mode browsing (chromium-browser package)
- **Openbox:** Minimal window manager (openbox package)
- **X11:** Display server (xserver-xorg-core, xinit)

## References

- Main concept doc: `Raspi_Concept` (always kept current)
- PyQt5 docs: https://doc.qt.io/qtforpython/
- DietPi software: https://dietpi.com/docs/software/
- Pi2 specs: 900MHz quad-core ARM Cortex-A7, 1GB RAM, VideoCore IV GPU
