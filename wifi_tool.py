"""
wifi_tool.py - Flask backend for the Wi-Fi diagnostic web UI.
Cross-platform (macOS / Windows 11).

Scan priority:
  1. WLANPi SSH -> iw dev <WLANPI_SCAN_IFACE> scan (2.4 + 5 GHz only)
  2. CoreWLAN (macOS) / netsh (Windows) native fallback

Run:
    pip install flask paramiko
    python wifi_tool.py
    open http://127.0.0.1:5000
"""

import re
import threading
import time
import sys
import atexit
from flask import Flask, jsonify, render_template, request

# ---------------------------------------------------------------------------
# wifi_utils v3.0 import guard
# ---------------------------------------------------------------------------
try:
    import wifi_utils as _wu
    _ver = getattr(_wu, "VERSION", "0.0")
    if _ver < "3.0":
        raise ImportError(f"wifi_utils version {_ver} is too old — replace with v3.0")
    _wu.startup_check()
    from wifi_utils import (
        wlanpi,
        scan_cache,
        shutdown,
        PLATFORM,
        analyse_network,
    )
except ImportError as e:
    raise SystemExit(
        f"\n  {e}\n"
        "  Make sure wifi_utils.py (v3.0) is in the same folder and paramiko is installed.\n"
    )

import os as _os
import sys as _sys


def _resource_path(relative: str) -> str:
    """Resolve path for both normal execution and PyInstaller .app bundle."""
    base = getattr(_sys, "_MEIPASS", _os.path.dirname(_os.path.abspath(__file__)))
    return _os.path.join(base, relative)


_templates_dir = _os.environ.get("RFDIAG_TEMPLATES", _resource_path("templates"))
app = Flask(__name__, template_folder=_templates_dir)

# ---------------------------------------------------------------------------
# ★ CONFIGURATION
# ---------------------------------------------------------------------------
# Auto-detect WLANPi scan interface
def _detect_wlanpi_iface():
    for iface in ["wlan1", "wlan0", "wlan2"]:
        try:
            out, _ = wlanpi.run(f"iw dev {iface} info 2>/dev/null")
            if iface in out:
                print(f"[WLANPi] Auto-detected interface: {iface}")
                return iface
        except Exception:
            pass
    print("[WLANPi] Could not auto-detect interface, defaulting to wlan1")
    return "wlan1"

WLANPI_SCAN_IFACE = None  # Auto-detected at scan time

# Windows only: specify which Wi-Fi adapter netsh should use for scanning.
# Set to None to use Windows default, or e.g. "Wi-Fi 3" for a specific adapter.
# Find your adapter name with: netsh wlan show interfaces
NETSH_INTERFACE = None   # None = Windows default adapter; set to "Wi-Fi 3" for USB Wi-Fi 7

# 6 GHz starts at 5925 MHz — anything at or above is excluded from WLANPi scan
FREQ_6GHZ_MIN = 5925


# ---------------------------------------------------------------------------
# WLANPi iw scan  (2.4 + 5 GHz only — 6 GHz excluded)
# ---------------------------------------------------------------------------

def scan_wlanpi_full() -> list[dict]:
    # Try interfaces in order until one returns results
    global WLANPI_SCAN_IFACE
    output = ""
    for _iface in ([WLANPI_SCAN_IFACE] if WLANPI_SCAN_IFACE else ["wlan1", "wlan0", "wlan2"]):
        try:
            wlanpi.run(f"sudo /sbin/ip link set {_iface} up 2>/dev/null || true")
            _out, _ = wlanpi.run(f"sudo iw dev {_iface} scan 2>/dev/null")
            if _out.strip():
                output = _out
                if WLANPI_SCAN_IFACE != _iface:
                    WLANPI_SCAN_IFACE = _iface
                    print(f"[WLANPi] Auto-detected interface: {_iface}")
                break
        except Exception:
            pass
    try:
        pass
    except RuntimeError as e:
        print(f"[WLANPi] {e}")
        return []

    if not output.strip():
        return []

    networks, current = [], {}
    in_bss_load = False

    for line in output.splitlines():
        s = line.strip()

        m = re.match(r"^BSS ([0-9a-f:]{17})", s, re.IGNORECASE)
        if m:
            if current.get("ssid") and current.get("bssid"):
                networks.append(current)
            current = {
                "bssid": m.group(1).lower(), "ssid": "",
                "rssi": -100, "channel": 1, "_freq": 0,
                "ap_tx_dbm": None, "ch_util_pct": None, "station_count": None,
                "ap_basic_rates": [], "ap_all_rates": [], "ap_min_basic_rate": None,
            }
            in_bss_load = False
            continue
        if not current:
            continue

        m = re.match(r"freq:\s*([\d.]+)", s)
        if m:
            freq = int(float(m.group(1)))
            current["_freq"] = freq
            current["freq_mhz"] = freq   # keep for band detection in analyse_network
            if freq >= FREQ_6GHZ_MIN:
                # 6 GHz channel number: (freq - 5950) / 5
                current["channel"] = (freq - 5950) // 5
            elif 2400 <= freq <= 2500:
                current["channel"] = (freq - 2407) // 5
            elif 5000 <= freq < FREQ_6GHZ_MIN:
                current["channel"] = (freq - 5000) // 5
            in_bss_load = False
            continue

        m = re.match(r"signal:\s*([-\d.]+)\s*dBm", s)
        if m:
            current["rssi"] = int(float(m.group(1)))
            in_bss_load = False
            continue

        m = re.match(r"SSID:\s*(.*)", s)
        if m:
            ssid = m.group(1).strip()
            if ssid:
                current["ssid"] = ssid
            in_bss_load = False
            continue

        for pattern in [
            r"TPC report:.*TX power:\s*(-?\d+)\s*dBm",
            r"Maximum TX Power:\s*(-?\d+)\s*dBm",
            r"\*\s*maximum TX power:\s*(-?\d+)\s*dBm",
            r"Channels\s*\[\d[\d\s-]*\]\s*@\s*(-?\d+)\s*dBm",  # Country IE
        ]:
            m = re.search(pattern, s, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                # Country IE: take highest value seen (covers scanned channel)
                # TPC/MaxTX: first match wins (highest priority)
                if current.get("ap_tx_dbm") is None or val > current["ap_tx_dbm"]:
                    current["ap_tx_dbm"] = val
                in_bss_load = False
                break

        m = re.match(r"Supported rates:\s*(.+)", s, re.IGNORECASE)
        if m:
            raw = m.group(1).split()
            basic = [float(r.rstrip("*")) for r in raw if r.endswith("*")]
            all_r = [float(r.rstrip("*")) for r in raw]
            current["ap_basic_rates"] = basic
            current["ap_all_rates"]   = all_r
            if basic:
                current["ap_min_basic_rate"] = min(basic)
            in_bss_load = False
            continue

        m = re.match(r"Extended supported rates:\s*(.+)", s, re.IGNORECASE)
        if m:
            raw = m.group(1).split()
            for r in raw:
                val = float(r.rstrip("*"))
                current["ap_all_rates"].append(val)
                if r.endswith("*"):
                    current["ap_basic_rates"].append(val)
            if current["ap_basic_rates"]:
                current["ap_min_basic_rate"] = min(current["ap_basic_rates"])
            in_bss_load = False
            continue

        if re.match(r"BSS Load:", s, re.IGNORECASE):
            in_bss_load = True
            continue

        if in_bss_load:
            m = re.match(r"\*\s*station count:\s*(\d+)", s, re.IGNORECASE)
            if m:
                current["station_count"] = int(m.group(1))
                continue
            m = re.match(r"\*\s*channel utilis[ae]tion:\s*(\d+)/255", s, re.IGNORECASE)
            if m:
                current["ch_util_pct"] = round(int(m.group(1)) / 255 * 100, 1)
                continue
            if not s.startswith("*"):
                in_bss_load = False

    if current.get("ssid") and current.get("bssid"):
        networks.append(current)

    # Remove internal keys (prefixed with _) but keep freq_mhz
    networks = [
        {k: v for k, v in n.items() if not k.startswith("_")}
        for n in networks
        if not n.get("_skip")
    ]

    networks.sort(key=lambda n: n["rssi"], reverse=True)
    util_count = sum(1 for n in networks if n["ch_util_pct"] is not None)
    print(f"[WLANPi] iw scan ({WLANPI_SCAN_IFACE}): {len(networks)} networks, "
          f"{util_count} with QBSS util.")
    return networks


# ---------------------------------------------------------------------------
# Cache refresh
# ---------------------------------------------------------------------------

_cache: dict = {
    "networks": [], "wlanpi_ssids": [], "wlanpi_ok": False,
    "scan_source": "none", "last_updated": None, "connected_ap": None,
}
_lock = threading.Lock()
_refresh_lock = threading.Lock()


def refresh_cache():
    if not _refresh_lock.acquire(blocking=False):
        print("[Refresh] Skip duplicate background scan.")
        return
    try:
        _do_refresh_cache()
    finally:
        _refresh_lock.release()


def _do_refresh_cache():
    raw    = scan_wlanpi_full()
    source = "wlanpi"

    if not raw:
        snapshot = scan_cache.snapshot()
        raw = [
            {
                "ssid":          n.get("ssid") or "",
                "bssid":         (n.get("bssid") or "").lower(),
                "rssi":          int(n.get("rssi") or -100),
                "channel":       int(n.get("channel") or 1),
                "freq_mhz":      n.get("freq_mhz"),   # preserve for 6 GHz detection
                "band":          n.get("band"),        # preserve corrected band
                "ap_tx_dbm":     None,
                "ch_util_pct":   n.get("ch_util_pct"),
                "station_count": n.get("station_count"),
            }
            for n in snapshot["networks"]
            if n.get("ssid") and n.get("bssid")
        ]
        source = PLATFORM

    connected_ap = scan_cache.connected_ap   # dict or None

    pi_ssids  = {n["ssid"] for n in raw} if source == "wlanpi" else set()
    wlanpi_ok = source == "wlanpi"

    enriched = []
    for n in raw:
        try:
            data = analyse_network(n, active_mbr_mbps=None,
                                   ap_tx_dbm=n.get("ap_tx_dbm"),
                                   ap_min_basic_rate=n.get("ap_min_basic_rate"),
                                   ap_basic_rates=n.get("ap_basic_rates", []),
                                   ap_all_rates=n.get("ap_all_rates", []))
            data["seen_by_wlanpi"] = wlanpi_ok
            data["ch_util_pct"]    = n.get("ch_util_pct")
            data["station_count"]  = n.get("station_count")
            enriched.append(data)
        except Exception as e:
            print(f"[Enrich] {e}")

    with _lock:
        _cache.update({
            "networks":     enriched,
            "wlanpi_ssids": sorted(pi_ssids),
            "wlanpi_ok":    wlanpi_ok,
            "scan_source":  source,
            "last_updated": time.strftime("%H:%M:%S"),
            "connected_ap": connected_ap,
        })
    print(f"[Cache] {len(enriched)} networks via {source}.")


def background_refresher():
    while True:
        try:
            refresh_cache()
        except Exception as e:
            print(f"[Refresh] {e}")
        time.sleep(30)


def wlanpi_prober():
    """Probe WLANPi every 10 s via TCP port 22. Auto-scan when first detected."""
    was_reachable = False
    while True:
        try:
            now_reachable = wlanpi.probe()
            if now_reachable and not was_reachable:
                print("[WLANPi] Device connected — triggering auto-scan.")
                threading.Thread(target=refresh_cache, daemon=True).start()
            elif not now_reachable and was_reachable:
                print("[WLANPi] Device disconnected.")
            was_reachable = now_reachable
        except Exception as e:
            print(f"[WLANPi Probe] {e}")
        time.sleep(10)


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan")
def api_scan():
    with _lock:
        return jsonify(_cache)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    threading.Thread(target=refresh_cache, daemon=True).start()
    return jsonify({"status": "refreshing"})


@app.route("/api/rssi")
def api_rssi():
    """Fast RSSI lookup for survey — returns current cached RSSI for requested SSIDs."""
    ssids = request.args.getlist("ssid")
    with _lock:
        networks = _cache.get("networks", [])
    result = {}
    for ssid in ssids:
        match = next((n for n in networks if n.get("ssid") == ssid), None)
        result[ssid] = match["rssi"] if match else None
    return jsonify(result)


@app.route("/api/status")
def api_status():
    return jsonify({
        "available":  wlanpi.available,
        "reachable":  wlanpi.reachable,
        "scan_iface": WLANPI_SCAN_IFACE,
        "status":     wlanpi.get_status() if wlanpi.available else {},
        "qbss":       wlanpi.get_qbss()   if wlanpi.available else [],
    })


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def main():
    """Start RF-DIAG. Called directly or from app_launcher.py (.app bundle)."""
    atexit.register(shutdown)
    scan_cache.netsh_interface = NETSH_INTERFACE  # Windows adapter config
    scan_cache.start()

    print(f"Platform: {sys.platform}")
    print(f"WLANPi scan interface: {WLANPI_SCAN_IFACE}")
    print("Running initial scan...")
    time.sleep(10)
    wlanpi.probe()  # Ensure WLANPi is detected before first scan
    refresh_cache()

    n   = len(_cache["networks"])
    src = _cache["scan_source"]
    print(f"Found {n} networks via {src}.")
    print("WLANPi: not connected / unavailable" if not wlanpi.available else f"WLANPi OK [{WLANPI_SCAN_IFACE}]")

    threading.Thread(target=background_refresher, daemon=True).start()
    threading.Thread(target=wlanpi_prober, daemon=True).start()
    app.run(host="0.0.0.0", debug=False, port=5001)


if __name__ == "__main__":
    main()
