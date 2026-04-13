# RF·DIAG — Wi-Fi Diagnostic Tool

A local web-based Wi-Fi diagnostic tool for macOS and Windows.  
Scan nearby networks, analyse RF health, run site surveys, and export PDF reports — all from a browser tab.

![RF-DIAG screenshot](screenshot.png)

---

## Features

| Feature | Description |
|---------|-------------|
| **Live Wi-Fi scan** | CoreWLAN (macOS) or netsh (Windows) — auto-selected |
| **WLANPi integration** | SSH-based `iw scan` via USB RNDIS for full QBSS/TX-power data |
| **Network table** | Sortable by SSID, RSSI, Channel, Distance, MBR, CH Util, CCC |
| **RF analysis** | Distance estimate (log-distance model), MBR thresholds, TX-power advice |
| **CCC detection** | Co-channel interference neighbours per network |
| **Wi-Fi Survey** | Floor plan heatmap (IDW), dual-SSID, threshold contour, calibration |
| **PDF report** | Full survey report with map, stats, and MBR coverage |
| **6 GHz support** | Correct band detection via `channelBand()` (Wi-Fi 6E / Wi-Fi 7) |
| **Location Services** | Header badge shows grant status on macOS 14+ (Sonoma) |

---

## Requirements

- **macOS** 12+ (Monterey or later) — tested on macOS 14 Sonoma
- Python 3.12 (recommended; CoreWLAN works reliably on 3.12)

```
pip install flask paramiko pyobjc-framework-CoreWLAN
```

---

## Quick Start (Terminal)

```bash
cd ~
source venv312/bin/activate
python wifi_tool.py
# Open http://127.0.0.1:5001
```

> **Note:** Running from Terminal on macOS 14+ will return networks but SSIDs may be blank.  
> See [macOS Location Services](#macos-location-services-sonoma-14) below for the fix.

---

## macOS Location Services (Sonoma 14+)

On macOS 14+, CoreWLAN requires **Location Services** permission to return SSIDs.  
Terminal apps do not appear in the Location Services list — you must package the app as a `.app` bundle.

### Build the .app bundle (one-time)

```bash
cd ~
source venv312/bin/activate
pip install pyinstaller
python -m PyInstaller RF_DIAG.spec --noconfirm
open dist/RF-DIAG.app
```

On first launch macOS will ask:  
*"RF-DIAG would like to use your location"* → click **Allow**

After granting permission, `dist/RF-DIAG.app` can be double-clicked at any time.  
The browser opens automatically at `http://127.0.0.1:5001`.

### If RF-DIAG doesn't appear in Location Services

Go to **System Settings → Privacy & Security → Location Services** and check.  
If missing: launch the `.app` once — the permission request registers the app automatically.

---

## WLANPi Integration

Connect a [WLANPi](https://www.wlanpi.com) via USB (RNDIS / 169.254.42.1).  
RF·DIAG will SSH into it and run `iw dev wlan1 scan` to obtain:

- Full QBSS channel utilisation
- Station counts
- AP TX power (TPC / Country IE)

Edit `wifi_tool.py` to change the scan interface:

```python
WLANPI_SCAN_IFACE = "wlan1"   # or wlan0, wlan2
```

SSH key used: `~/.ssh/id_ed25519`

---

## Project Structure

```
~/
├── wifi_tool.py          # Flask backend (routes, cache, WLANPi scan)
├── wifi_utils.py         # RF analysis, CoreWLAN, netsh, WLANPiSSH class
├── app_launcher.py       # PyInstaller .app entry point + Location Services request
├── RF_DIAG.spec          # PyInstaller build spec
├── entitlements.plist    # macOS network entitlements
├── build_mac.sh          # One-shot build script
└── templates/
    └── index.html        # Single-page UI (vanilla JS, no framework)
```

---

## Building

```bash
bash build_mac.sh
```

Installs dependencies, cleans previous build, produces `dist/RF-DIAG.app`.

---

## Windows

Use `netsh` backend — no build step required:

```bat
pip install flask paramiko
python wifi_tool.py
```

To use a specific Wi-Fi adapter, set in `wifi_tool.py`:

```python
NETSH_INTERFACE = "Wi-Fi 3"   # or None for default
```

---

## License

MIT
