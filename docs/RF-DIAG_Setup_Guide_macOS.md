# RF-DIAG Complete Setup Guide (macOS)
Full CLI Breakdown — Installation, Configuration & Fixes

---

## Prerequisites

- macOS 12+ (Monterey or later), tested on macOS 14 Sonoma
  - Internet connection
  - WLANPi device (optional — for full scan features)

---

## PART 1 — Install Homebrew

Homebrew is a package manager for macOS. Open **Terminal** and run:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Enter your Mac login password when prompted. You won't see characters as you type — that's normal.

Verify Homebrew installed correctly:
```
brew --version
```

---

## PART 2 — Install Python 3.12

```
brew install python@3.12
```

Verify Python installed correctly:
```
python3.12 --version
```

---

## PART 3 — Clone the RF-DIAG Repository

```
cd ~
git clone https://github.com/adaigle18/RF-DIAG.git
cd RF-DIAG
```

---

## PART 4 — Create Virtual Environment & Install Dependencies

```
# Go to home directory
cd ~

# Create virtual environment with Python 3.12
python3.12 -m venv venv312

# Activate the virtual environment
source venv312/bin/activate

# Go into the RF-DIAG folder
cd RF-DIAG

# Install required packages
pip install flask paramiko pyobjc-framework-CoreWLAN pyinstaller
```

You should see **(venv312)** at the start of your terminal prompt when the virtual environment is active.

---

## PART 5 — SSH Key Setup (WLANPi only)

The app connects to the WLANPi automatically via SSH key authentication.
Copy your public key to the WLANPi once (you will be prompted for the WLANPi password):

```
ssh-copy-id wlanpi@169.254.42.1
```

Default WLANPi password: **wlanpi**

Test the connection (should connect without asking for a password):
```
ssh wlanpi@169.254.42.1
exit
```

> **Note:** RF-DIAG automatically tries both `169.254.42.1` (R4/Go link-local) and
> `198.18.42.1` (RNDIS static) — no manual IP configuration needed.

---

## PART 6 — USB Wi-Fi Adapter (WLANPi only)

RF-DIAG scans using `iw dev scan`, which requires an adapter in **managed mode**.

- `wlan0` on the WLANPi is typically in **monitor mode** — it cannot perform active scans.
- Plug in a **USB Wi-Fi adapter** — it will appear as `wlan1` and RF-DIAG will use it automatically.

RF-DIAG auto-detects the scan interface by trying `wlan1`, `wlan0`, `wlan2` in order.
No manual configuration needed.

---

## PART 7 — Build the .app Bundle (Required for macOS 14+ Sonoma)

On macOS 14+, Location Services permission is required for SSIDs to appear.
Build the `.app` bundle to enable this:

```
cd ~
source venv312/bin/activate
cd RF-DIAG
python -m PyInstaller RF_DIAG.spec --noconfirm
open dist/RF-DIAG.app
```

When prompted, click **Allow** for Location Services.

After granting permission, you can double-click `dist/RF-DIAG.app` at any time.

---

## Every Time You Want to Run the App

Simply double-click `dist/RF-DIAG.app`.

The browser opens automatically at `http://127.0.0.1:5001`.
Startup takes approximately **20 seconds** (Location Services init + initial Wi-Fi scan).

You can plug in the WLANPi **before or after** launching — RF-DIAG detects it automatically within 10 seconds.

---

## Troubleshooting Quick Reference

| Problem | Fix |
|---|---|
| `brew: command not found` | Install Homebrew (Part 1) |
| `venv312: no such file` | Create virtual environment (Part 4) |
| `TypeErrors / unsupported operand` | Virtual environment not using Python 3.12 — recreate venv |
| `Blank SSIDs` | Build .app bundle (Part 7) and grant Location Services |
| `Port 5001 already in use` | Run `lsof -i :5001` then `kill -9 PID` |
| WLANPi not detected | Check USB cable; wait 10 s for auto-detection |
| WLANPi SSH connect failed | Run `ssh-copy-id wlanpi@169.254.42.1` (Part 5) |
| WLANPi reachable but 0 networks | Plug in USB Wi-Fi adapter for managed-mode scanning (Part 6) |
| SSH host key mismatch (after WLANPi reflash) | Run `ssh-keygen -R 169.254.42.1` then restart app |
| `wlan0: Operation not supported` | wlan0 is in monitor mode — use USB adapter (wlan1) |
| `0 networks via darwin` | Activate venv: `source ~/venv312/bin/activate` |

---

*RF·DIAG — Réseaux Eagle — May 2026*
