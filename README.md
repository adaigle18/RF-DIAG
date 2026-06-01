# RF·DIAG — Wi-Fi Diagnostic Tool

A local web-based Wi-Fi diagnostic tool for macOS and Windows.  
Scan nearby networks, analyse RF health, run site surveys, and export PDF reports — all from a browser tab.

<img width="1490" height="614" alt="Screenshot 2026-04-13 at 11 19 19 AM" src="https://github.com/user-attachments/assets/6f16bc52-6a35-48b0-9582-daa70a712fe4" />



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
- **WLANPi (optional):** requires **two Wi-Fi adapters** — the built-in adapter runs in monitor mode and cannot scan; a USB Wi-Fi adapter (`wlan1`) is required for active scanning

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

> **Two Wi-Fi adapters required.**  
> The WLANPi's built-in adapter (`wlan0`) runs in monitor mode and cannot perform active scans.  
> You must plug in a **USB Wi-Fi adapter** — it will appear as `wlan1` and RF·DIAG will use it automatically.  
> Without a second adapter, the WLANPi will be detected via SSH but no networks will be returned.

Connect a [WLANPi](https://www.wlanpi.com) via USB (RNDIS).  
RF·DIAG will SSH into it and run `iw dev scan` to obtain:

- Full QBSS channel utilisation
- Station counts
- AP TX power (TPC / Country IE)
- Min Basic Rate and full rate set per AP

**When WLANPi is connected, it takes full priority — the native CoreWLAN/netsh scan is paused automatically.**  
If the WLANPi disconnects, RF·DIAG falls back to the native scan with no intervention required.

### Auto-detection

RF·DIAG probes for the WLANPi every 10 seconds — you can plug it in at any time, before or after launching the app:
- **IP address** — tries `169.254.42.1` (R4/Go link-local) then `198.18.42.1` (RNDIS static) every cycle
- **Scan interface** — tries `wlan1`, `wlan0`, `wlan2` in order and locks on to whichever returns data

No manual configuration needed for standard WLANPi setups.

### SSH Key Setup (one-time)

RF·DIAG connects via SSH key authentication automatically (tries `id_ed25519` then `id_rsa`).  
Copy your public key to the WLANPi once — replace `your_key.pub` with your actual public key filename:

```bash
ssh-copy-id wlanpi@169.254.42.1
```

After this, RF·DIAG connects automatically without a password prompt.

### USB Wi-Fi Adapter Requirement

RF·DIAG scans using `iw dev scan`, which requires an adapter in **managed mode**.

> **Recommended: two Wi-Fi adapters on the WLANPi.**  
> `wlan0` is typically the built-in adapter running in monitor mode — it cannot perform active scans.  
> Plug in a USB Wi-Fi adapter (it will appear as `wlan1`) and RF·DIAG will use it automatically for scanning.  
> Single-adapter setups work only if that adapter is in managed mode.

### Troubleshooting

**WLANPi not detected after reflash or replacement**

If the WLANPi's SSH host key has changed, you will see a "host key mismatch" error. Clear the old entry and reconnect:

```bash
ssh-keygen -R 169.254.42.1
```

Then restart RF·DIAG — it will re-accept the new host key automatically.

**Scan returns no networks despite WLANPi being reachable**

Check that the scanning adapter (`wlan1`) is in managed mode:

```bash
ssh wlanpi@169.254.42.1 "iw dev"
```

Look for `type managed` next to your scan interface. If it shows `type monitor`, plug in a USB Wi-Fi adapter.

**0 networks after rebuild (macOS)**

After rebuilding the `.app`, a stale process from the previous build may still be running on port 5001.
The new app detects the port is in use and skips startup — so Location Services is never re-requested.

Force-quit all instances before launching a new build:

```bash
pkill -9 -f RF-DIAG
```

Then open `dist/RF-DIAG.app` normally. If RF-DIAG still doesn't appear in Location Services, go to
**System Settings → Privacy & Security → Location Services**, toggle RF-DIAG off and back on, then restart the app.

**0 networks with no WLANPi (macOS)**

RF·DIAG requires Location Services permission to return SSIDs via CoreWLAN.  
Go to **System Settings → Privacy & Security → Location Services** and ensure RF-DIAG is enabled.  
If it doesn't appear, launch `dist/RF-DIAG.app` once — the permission request registers it automatically.

Without a WLANPi, RF·DIAG falls back to:
- **MBR** — estimated from RSSI thresholds (not the actual AP-advertised rate)
- **TX Power** — defaulted to 20 dBm (affects distance calculation accuracy)
- **Basic rates** — not available (requires `iw scan` output)

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

## Documentation

- [macOS Setup Guide](docs/RF-DIAG_Setup_Guide_macOS.md) — step-by-step setup including Location Services, PyInstaller build, and WLANPi connection
- [Windows Setup Guide](docs/RF-DIAG_Guide_Windows.md) — installation guide for Windows 10/11 with and without WLANPi (French)

---

## License

MIT
