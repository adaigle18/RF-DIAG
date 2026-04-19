"""
wifi_utils.py  v3.0
Cross-platform Wi-Fi utility library for RF·DIAG
Supports: macOS (CoreWLAN) and Windows (netsh)
WLANPi integration via Paramiko SSH (replaces ControlMaster)
"""

import sys
import json
import threading
import subprocess
import time
import re
import logging

log = logging.getLogger(__name__)

PLATFORM = sys.platform  # "darwin" | "win32" | "linux"

# ---------------------------------------------------------------------------
# Version banner
# ---------------------------------------------------------------------------
VERSION = "3.1"


# ===========================================================================
# RF Analysis  (ported from wifi_utils v2.0)
# ===========================================================================

import math

DEFAULT_TX_POWER_DBM     = 20
DEFAULT_ANTENNA_GAIN_DBI = 2
PATH_LOSS_EXP            = 3.5
ATTENUATION_FACTOR_DB    = 3

MBR_THRESHOLDS      = {24: -74, 12: -79, 6: -82}
RETRY_RISK_RSSI     = -70
POWER_INCREASE_RSSI = -67
CCI_CAUTION_RSSI    = -55
MAX_SAFE_TX_DBM     = 23


def _fspl_ref_1m(frequency_mhz, tx_power_dbm, antenna_gain_dbi):
    fspl_1m = 20 * math.log10(frequency_mhz * 1e6) - 147.55
    return tx_power_dbm + antenna_gain_dbi - fspl_1m


def estimate_distance(rssi_dbm, frequency_mhz=2437,
                      tx_power_dbm=DEFAULT_TX_POWER_DBM,
                      antenna_gain_dbi=DEFAULT_ANTENNA_GAIN_DBI,
                      n=PATH_LOSS_EXP):
    rssi_ref = _fspl_ref_1m(frequency_mhz, tx_power_dbm, antenna_gain_dbi)
    return round(max(10 ** ((rssi_ref - rssi_dbm) / (10 * n)), 0.1), 1)


def distance_label(d):
    if d < 5:  return "Very close"
    if d < 15: return "Near"
    if d < 30: return "Mid-range"
    if d < 60: return "Far"
    return "Very far"


def is_2_4ghz(channel, freq_mhz=None):
    if freq_mhz: return 2400 <= freq_mhz <= 2500
    return 1 <= channel <= 14

def is_5ghz(channel, freq_mhz=None):
    if freq_mhz: return 5000 <= freq_mhz < 5925
    return 36 <= channel <= 177

def is_6ghz(channel, freq_mhz=None):
    if freq_mhz: return freq_mhz >= 5925
    return not is_2_4ghz(channel) and not is_5ghz(channel)

def band_label(channel, freq_mhz=None):
    if is_2_4ghz(channel, freq_mhz): return "2.4 GHz"
    if is_5ghz(channel, freq_mhz):   return "5 GHz"
    return "6 GHz"


def channel_to_frequency_mhz(channel):
    if 1  <= channel <= 13:  return 2412 + (channel - 1) * 5
    if channel == 14:        return 2484
    if 36 <= channel <= 177: return 5000 + channel * 5
    # 6 GHz: channel 1 = 5955 MHz, step 5 MHz
    if channel >= 1:         return 5950 + channel * 5
    return 5180


def supported_mbr_rates(rssi_dbm):
    return [r for r, thr in MBR_THRESHOLDS.items() if rssi_dbm >= thr]


def best_supported_mbr(rssi_dbm):
    rates = supported_mbr_rates(rssi_dbm)
    return max(rates) if rates else None


def mbr_status(rssi_dbm, active_mbr_mbps=None):
    rates    = supported_mbr_rates(rssi_dbm)
    best     = best_supported_mbr(rssi_dbm)
    mismatch = best is not None and active_mbr_mbps is not None and active_mbr_mbps < best
    return {
        "supported_rates": sorted(rates, reverse=True),
        "best_supported":  best,
        "active_mbr":      active_mbr_mbps,
        "active_ok":       active_mbr_mbps is not None and active_mbr_mbps >= 6,
        "supported_label": f"{best} Mbps" if best else "Below 6 Mbps (marginal)",
        "active_label":    f"{active_mbr_mbps} Mbps" if active_mbr_mbps is not None else "Unknown",
        "mismatch":        mismatch,
        "ok":              best is not None,
        "best_mbr":        best,
        "label":           f"{best} Mbps" if best else "Below 6 Mbps (marginal)",
    }



def basic_rate_optimization(ap_min_basic_rate=None, ap_basic_rates=None, ap_all_rates=None):
    """
    Analyse the AP's advertised minimum basic rate and return an optimization
    recommendation. Basic rates are the rates used for management frames (beacons,
    probe responses, etc.). Lower basic rates waste more airtime.

    Best practice: set minimum basic rate to 12 Mbps (disables 1/2/5.5/11 Mbps CCK).
    All 802.11g/n/ac/ax devices support 12 Mbps.
    """
    rates  = ap_basic_rates or []
    all_r  = ap_all_rates   or []

    if ap_min_basic_rate is None:
        return {
            "min_basic_rate":   None,
            "basic_rates":      rates,
            "all_rates":        all_r,
            "severity":         "unknown",
            "label":            "N/A",
            "advice":           "Basic rates not available — connect WLANPi for iw scan data.",
            "recommended_min":  12,
            "needs_change":     False,
        }

    r = float(ap_min_basic_rate)

    if r <= 2:
        sev   = "danger"
        needs = True
        advice = (f"Min basic rate = {r} Mbps (CCK legacy). "
                  "Beacons & management frames sent at 1-2 Mbps waste significant airtime. "
                  "Raise to 12 Mbps — all 802.11g/n/ac/ax clients support it. "
                  "Expected gain: 30-50% more usable airtime.")
    elif r <= 5.5:
        sev   = "danger"
        needs = True
        advice = (f"Min basic rate = {r} Mbps (CCK). "
                  "CCK rates still active — management frames are slow. "
                  "Raise to 12 Mbps to disable CCK and free airtime.")
    elif r < 12:
        sev   = "warn"
        needs = True
        advice = (f"Min basic rate = {r} Mbps (OFDM but suboptimal). "
                  "Raising to 12 Mbps reduces management overhead further.")
    elif r < 24:
        sev   = "good"
        needs = False
        advice = (f"Min basic rate = {r} Mbps — good. "
                  "Management frames are airtime-efficient. "
                  "Consider 24 Mbps for dense or enterprise environments.")
    else:
        sev   = "good"
        needs = False
        advice = (f"Min basic rate = {r} Mbps — optimal. "
                  "Minimum overhead for management frames.")

    return {
        "min_basic_rate":  r,
        "basic_rates":     sorted(rates),
        "all_rates":       sorted(all_r),
        "severity":        sev,
        "label":           f"{r} Mbps",
        "advice":          advice,
        "recommended_min": 12 if needs else None,
        "needs_change":    needs,
    }

def power_recommendation(rssi_dbm, channel, ap_tx_dbm=None):
    tx_str = f"{ap_tx_dbm} dBm" if ap_tx_dbm is not None else "unknown"
    if rssi_dbm > CCI_CAUTION_RSSI:
        return {"retry_risk": False, "action": tx_str, "severity": "good",
                "advice": f"Signal is strong (AP TX: {tx_str}). Do not raise Tx power - risk of CCI.",
                "rssi": rssi_dbm, "ap_tx_dbm": ap_tx_dbm, "suggested_tx": None}
    if rssi_dbm >= POWER_INCREASE_RSSI:
        return {"retry_risk": False, "action": tx_str, "severity": "warning",
                "advice": f"Signal is acceptable (AP TX: {tx_str}). Monitor retry counters.",
                "rssi": rssi_dbm, "ap_tx_dbm": ap_tx_dbm, "suggested_tx": None}
    if ap_tx_dbm is not None:
        suggested = min(ap_tx_dbm + 6, MAX_SAFE_TX_DBM)
        delta = suggested - ap_tx_dbm
        action = f"{ap_tx_dbm}+{delta} dBm" if delta > 0 else f"{ap_tx_dbm} dBm (max)"
        advice = (f"Signal is weak. Raise AP TX to {suggested} dBm." if delta > 0
                  else f"Signal weak but AP at max ({ap_tx_dbm} dBm). Add AP or move closer.")
        return {"retry_risk": True, "action": action, "severity": "danger",
                "advice": advice, "rssi": rssi_dbm, "ap_tx_dbm": ap_tx_dbm, "suggested_tx": suggested}
    return {"retry_risk": True, "action": "INCREASE", "severity": "danger",
            "advice": "Signal is weak. Raise AP Tx power by 3-6 dBm.",
            "rssi": rssi_dbm, "ap_tx_dbm": ap_tx_dbm, "suggested_tx": None}


def analyse_network(n: dict, active_mbr_mbps=None, ap_tx_dbm=None,
                    ap_min_basic_rate=None, ap_basic_rates=None, ap_all_rates=None) -> dict:
    """Run all RF diagnostics on a single network dict."""
    rssi    = n["rssi"]
    channel = n["channel"]
    # Use stored frequency if available (most accurate for band detection)
    freq    = n.get("freq_mhz") or channel_to_frequency_mhz(channel)
    # Always use 2.4 GHz reference frequency for distance estimation so that
    # the same AP seen on multiple bands (2.4/5/6 GHz) yields a consistent
    # distance value rather than artificially shorter estimates on higher bands.
    dist    = estimate_distance(rssi, frequency_mhz=2437)
    tx      = ap_tx_dbm if ap_tx_dbm is not None else n.get("ap_tx_dbm")

    min_br  = ap_min_basic_rate if ap_min_basic_rate is not None else n.get("ap_min_basic_rate")
    br_list = ap_basic_rates    if ap_basic_rates    is not None else n.get("ap_basic_rates", [])
    all_r   = ap_all_rates      if ap_all_rates      is not None else n.get("ap_all_rates", [])

    return {
        **n,
        "distance_m":     dist,
        "distance_label": distance_label(dist),
        "attenuation_db": ATTENUATION_FACTOR_DB,
        "band":           band_label(channel, freq),
        "has_2_4ghz":     is_2_4ghz(channel, freq),
        "has_5ghz":       is_5ghz(channel, freq),
        "has_6ghz":       is_6ghz(channel, freq),
        "frequency_mhz":  freq,
        "mbr":            mbr_status(rssi, active_mbr_mbps=active_mbr_mbps),
        "power":          power_recommendation(rssi, channel, ap_tx_dbm=tx),
        "basic_rate_opt": basic_rate_optimization(min_br, br_list, all_r),
    }


def startup_check():
    log.info(f"[Startup] wifi_utils v{VERSION} OK")
    log.info(f"Platform: {PLATFORM}")


# ===========================================================================
# iw scan TX power / Country IE parser
# ===========================================================================

def parse_iw_scan_tx_power(iw_output: str) -> dict[str, int | None]:
    """
    Parse raw `iw scan` output and extract AP TX power (dBm) keyed by BSSID.

    Sources tried in priority order per BSS block:
      1. TPC Report IE          – "TPC report: TX power: X"
      2. Maximum Transmit Power IE – "Maximum TX Power: X dBm"
      3. Country IE channel entry  – "Channels [X - Y] @ Z dBm"  (takes the
         highest power listed, which covers the scanned channel in most cases)

    Returns dict mapping BSSID (upper-case, colon-separated) -> int dBm | None.
    """
    result: dict[str, int | None] = {}
    current_bssid: str | None = None
    tx_power: int | None = None

    # Patterns
    bssid_re    = re.compile(r"^BSS ([0-9A-Fa-f:]{17})\(", re.IGNORECASE)
    tpc_re      = re.compile(r"TPC report:\s*TX power:\s*(-?\d+)", re.IGNORECASE)
    max_tx_re   = re.compile(r"Maximum TX Power:\s*(-?\d+)\s*dBm", re.IGNORECASE)
    country_re  = re.compile(r"Channels\s*\[[\d\s-]*\]\s*@\s*(-?\d+)\s*dBm", re.IGNORECASE)

    for line in iw_output.splitlines():
        bssid_m = bssid_re.search(line)
        if bssid_m:
            # Save previous BSS
            if current_bssid is not None:
                result[current_bssid] = tx_power
            current_bssid = bssid_m.group(1).upper()
            tx_power = None
            continue

        if current_bssid is None:
            continue

        # Priority 1 – TPC Report IE (overrides everything)
        m = tpc_re.search(line)
        if m:
            tx_power = int(m.group(1))
            continue

        # Priority 2 – Maximum TX Power IE (only if not already set by TPC)
        if tx_power is None:
            m = max_tx_re.search(line)
            if m:
                tx_power = int(m.group(1))
                continue

        # Priority 3 – Country IE channel entry (take max value seen)
        m = country_re.search(line)
        if m:
            candidate = int(m.group(1))
            if tx_power is None or candidate > tx_power:
                tx_power = candidate

    # Save last BSS
    if current_bssid is not None:
        result[current_bssid] = tx_power

    return result


def enrich_networks_with_tx_power(networks: list[dict], iw_output: str) -> list[dict]:
    """
    Given a list of network dicts and raw `iw scan` output, inject
    'ap_tx_dbm' into each dict where the BSSID matches.
    Networks that already have a non-None 'ap_tx_dbm' are left unchanged.
    """
    tx_map = parse_iw_scan_tx_power(iw_output)
    for net in networks:
        bssid = (net.get("bssid") or "").upper()
        if net.get("ap_tx_dbm") is None and bssid in tx_map:
            net["ap_tx_dbm"] = tx_map[bssid]
    return networks


# ===========================================================================
# iw scan raw output parser  (used by WLANPiSSH.iw_scan_with_tx_power)
# ===========================================================================

def _parse_iw_scan_output(raw: str) -> list[dict]:
    """
    Parse raw `iw dev <iface> scan dump` output into a list of network dicts.
    Each dict contains: ssid, bssid, rssi, channel, band, freq, ap_tx_dbm,
                        qbss_utilization_pct, station_count, auth.
    """
    networks: list[dict] = []
    current: dict | None = None

    bssid_re   = re.compile(r"^BSS ([0-9A-Fa-f:]{17})\(", re.IGNORECASE)
    ssid_re    = re.compile(r"^\s+SSID:\s*(.*)")
    signal_re  = re.compile(r"^\s+signal:\s*(-[\d.]+)\s*dBm")
    freq_re    = re.compile(r"^\s+freq:\s*(\d+)")
    chan_re    = re.compile(r"^\s+DS Parameter set: channel\s+(\d+)")
    ht_chan_re = re.compile(r"^\s+\* primary channel:\s*(\d+)")
    bss_re     = re.compile(r"^\s+\* channel utilisation:\s*(\d+)/255")
    sta_re     = re.compile(r"^\s+\* station count:\s*(\d+)")
    rsn_re     = re.compile(r"^\s+RSN:")
    wpa_re     = re.compile(r"^\s+WPA:")
    tpc_re     = re.compile(r"TPC report:\s*TX power:\s*(-?\d+)", re.IGNORECASE)
    max_tx_re  = re.compile(r"Maximum TX Power:\s*(-?\d+)\s*dBm", re.IGNORECASE)
    country_re = re.compile(r"Channels\s*\[[\d\s-]*\]\s*@\s*(-?\d+)\s*dBm", re.IGNORECASE)

    def _save(c):
        if c and c.get("bssid"):
            if c.get("channel") is None and c.get("freq"):
                f = int(c["freq"])
                if 2412 <= f <= 2484:
                    c["channel"] = (f - 2407) // 5 if f != 2484 else 14
                elif 5000 <= f <= 5900:
                    c["channel"] = (f - 5000) // 5
            ch = c.get("channel") or 0
            c["band"] = "5 GHz" if ch > 14 else "2.4 GHz"
            networks.append(c)

    for line in raw.splitlines():
        m = bssid_re.search(line)
        if m:
            _save(current)
            current = {
                "bssid": m.group(1).upper(), "ssid": "", "rssi": None,
                "channel": None, "freq": None, "band": None,
                "ap_tx_dbm": None, "qbss_utilization_pct": None,
                "station_count": None, "auth": "Open",
            }
            continue

        if current is None:
            continue

        if (mm := ssid_re.match(line)):
            current["ssid"] = mm.group(1).strip()
        elif (mm := signal_re.match(line)):
            current["rssi"] = int(float(mm.group(1)))
        elif (mm := freq_re.match(line)):
            current["freq"] = int(mm.group(1))
        elif (mm := chan_re.match(line)):
            current["channel"] = int(mm.group(1))
        elif (mm := ht_chan_re.match(line)) and current["channel"] is None:
            current["channel"] = int(mm.group(1))
        elif (mm := bss_re.match(line)):
            current["qbss_utilization_pct"] = round(int(mm.group(1)) / 255 * 100, 1)
        elif (mm := sta_re.match(line)):
            current["station_count"] = int(mm.group(1))
        elif rsn_re.match(line):
            current["auth"] = "WPA2/WPA3"
        elif wpa_re.match(line) and current["auth"] == "Open":
            current["auth"] = "WPA"
        elif (mm := tpc_re.search(line)):
            current["ap_tx_dbm"] = int(mm.group(1))
        elif (mm := max_tx_re.search(line)) and current["ap_tx_dbm"] is None:
            current["ap_tx_dbm"] = int(mm.group(1))
        elif (mm := country_re.search(line)):
            candidate = int(mm.group(1))
            if current["ap_tx_dbm"] is None or candidate > current["ap_tx_dbm"]:
                current["ap_tx_dbm"] = candidate

    _save(current)
    return networks


# ===========================================================================
# WLANPi SSH  (Paramiko-based, cross-platform)
# ===========================================================================

class WLANPiSSH:
    """
    Persistent SSH connection to WLANPi over USB/RNDIS (198.18.42.1).
    Uses Paramiko so it works identically on macOS and Windows.
    Thread-safe: a single connection is reused across Flask threads.
    """

    def __init__(
        self,
        host: str = None,
        user: str = "wlanpi",
        key_path: str = None,
        password: str = None,
        connect_timeout: int = 15,
        exec_timeout: int = 30,
    ):
        # Auto-detect WLANPi IP if not specified
        if host is None:
            import socket as _s
            for _ip in ["169.254.42.1", "198.18.42.1"]:
                _sock = None
                try:
                    _sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    _sock.settimeout(2)
                    _sock.connect((_ip, 22))
                    host = _ip
                    print(f"[WLANPi] Auto-detected host: {host}")
                    break
                except Exception as _e:
                    log.debug(f"[WLANPi] {_ip} not reachable during init: {_e}")
                finally:
                    if _sock is not None:
                        try:
                            _sock.close()
                        except Exception:
                            pass
            if host is None:
                host = "169.254.42.1"  # default fallback
        self.host = host
        self.user = user
        self.password = password
        self.connect_timeout = connect_timeout
        self.exec_timeout = exec_timeout

        # Default key path per platform
        if key_path is None:
            if PLATFORM == "win32":
                import os
                key_path = os.path.expanduser(r"~\.ssh\id_rsa")
            else:
                import os
                key_path = os.path.expanduser("~/.ssh/id_rsa")
        self.key_path = key_path

        self._client = None
        self._lock = threading.Lock()
        self._available = False
        self._reachable = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_client(self):
        try:
            import paramiko
        except ImportError:
            raise RuntimeError(
                "paramiko is not installed. Run: pip install paramiko"
            )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = dict(
            hostname=self.host,
            username=self.user,
            timeout=self.connect_timeout,
            banner_timeout=30,
            auth_timeout=30,
        )

        import os
        if self.key_path and os.path.exists(self.key_path):
            kwargs["key_filename"] = self.key_path
            kwargs["look_for_keys"] = False
            kwargs["allow_agent"] = False
        elif self.password:
            kwargs["password"] = self.password
        else:
            # Fall back to SSH agent / default keys
            pass

        import socket as _socket
        _sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        _sock.settimeout(self.connect_timeout)
        try:
            _sock.bind((self._local_ip(), 0))
            _sock.connect((self.host, 22))
            kwargs["sock"] = _sock
            client.connect(**kwargs)
        except Exception:
            _sock.close()
            raise
        return client


    def _local_ip(self) -> str:
        """Find the local IP that routes to the WLANPi."""
        import socket as _s
        tmp = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
        try:
            tmp.connect((self.host, 22))
            return tmp.getsockname()[0]
        except Exception as e:
            log.debug(f"[WLANPi] Could not determine local IP for {self.host}: {e}")
            return "0.0.0.0"
        finally:
            tmp.close()
    def _is_alive(self) -> bool:
        if self._client is None:
            return False
        t = self._client.get_transport()
        return t is not None and t.is_active()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def probe(self) -> bool:
        """
        Fast reachability check: TCP connect to port 22, ~2 s timeout.
        Does NOT perform an SSH handshake.  Updates _reachable and closes
        any stale SSH client when the host goes away.
        Returns True if the WLANPi is reachable.
        """
        import socket
        reachable = False
        try:
            with socket.create_connection((self.host, 22), timeout=10):
                reachable = True
        except (OSError, socket.timeout):
            pass

        if reachable and not self._reachable:
            log.info(f"[WLANPi] Device detected at {self.host}")
        elif not reachable and self._reachable:
            log.info(f"[WLANPi] Device no longer reachable at {self.host}")
            with self._lock:
                self._available = False
                if self._client:
                    try:
                        self._client.close()
                    except Exception:
                        pass
                    self._client = None

        self._reachable = reachable
        return reachable

    @property
    def reachable(self) -> bool:
        """True if the last probe() found the WLANPi's SSH port open."""
        return self._reachable

    def run(self, command: str) -> tuple[str, str]:
        """
        Run a command on the WLANPi.
        Returns (stdout, stderr) as stripped strings.
        Raises RuntimeError on connection failure.
        """
        with self._lock:
            if not self._is_alive():
                try:
                    if self._client:
                        try:
                            self._client.close()
                        except Exception:
                            pass
                    self._client = self._make_client()
                    self._available = True
                    log.info(f"[WLANPi] Connected to {self.host}")
                except Exception as e:
                    self._client = None
                    self._available = False
                    raise RuntimeError(f"WLANPi SSH connect failed: {e}")

            try:
                _, stdout, stderr = self._client.exec_command(
                    command, timeout=self.exec_timeout
                )
                out = stdout.read().decode(errors="replace").strip()
                err = stderr.read().decode(errors="replace").strip()
                return out, err
            except Exception as e:
                self._client = None
                self._available = False
                raise RuntimeError(f"WLANPi SSH exec failed: {e}")

    @property
    def available(self) -> bool:
        return self._available and self._is_alive()

    def close(self):
        with self._lock:
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = None
                self._available = False
                log.info("[WLANPi] SSH connection closed")

    # ------------------------------------------------------------------
    # WLANPi-specific commands
    # ------------------------------------------------------------------

    def get_qbss(self) -> list[dict]:
        """
        Fetch QBSS channel utilization data from the WLANPi QBSS API.
        Returns a list of dicts: [{bssid, ssid, channel, utilization, ...}]
        """
        try:
            out, _ = self.run("curl -s http://127.0.0.1:8765/api/qbss")
            return json.loads(out) if out else []
        except Exception as e:
            log.warning(f"[WLANPi] QBSS fetch failed: {e}")
            return []

    def get_passive_scan(self) -> list[dict]:
        """
        Fetch passive scan results from wlan1 (monitor mode) via WLANPi API.
        Returns a list of BSS dicts.
        """
        try:
            out, _ = self.run("curl -s http://127.0.0.1:8765/api/scan")
            return json.loads(out) if out else []
        except Exception as e:
            log.warning(f"[WLANPi] Passive scan fetch failed: {e}")
            return []

    def get_status(self) -> dict:
        """
        Fetch WLANPi status from the QBSS API /api/status endpoint.
        """
        try:
            out, _ = self.run("curl -s http://127.0.0.1:8765/api/status")
            return json.loads(out) if out else {}
        except Exception as e:
            log.warning(f"[WLANPi] Status fetch failed: {e}")
            return {}

    def set_country_code(self, country: str = "CA") -> bool:
        """
        Set the regulatory country code on the WLANPi (e.g. 'CA', 'US', 'GB').
        Runs: sudo iw reg set <COUNTRY>
        Returns True on success, False on failure.

        NOTE: This only affects the kernel regulatory domain for the current
        session. Add 'REGDOMAIN=CA' to /etc/default/crda for persistence.
        """
        country = country.upper().strip()
        if not re.match(r"^[A-Z]{2}$", country):
            log.error(f"[WLANPi] Invalid country code: {country!r}")
            return False
        try:
            out, err = self.run(f"sudo /usr/sbin/iw reg set {country}")
            # Verify it was applied
            verify_out, _ = self.run("/usr/sbin/iw reg get")
            if country in verify_out:
                log.info(f"[WLANPi] Country code set to {country}")
                return True
            log.warning(f"[WLANPi] Country set command ran but '{country}' not confirmed in reg get")
            return False
        except Exception as e:
            log.warning(f"[WLANPi] set_country_code failed: {e}")
            return False

    def get_country_code(self) -> str | None:
        """
        Return the currently active regulatory country code from the WLANPi.
        Parses `iw reg get` output for the 'country XX:' line.
        """
        try:
            out, _ = self.run("/usr/sbin/iw reg get")
            m = re.search(r"^country\s+([A-Z]{2})\s*:", out, re.MULTILINE | re.IGNORECASE)
            if m:
                return m.group(1).upper()
            return None
        except Exception as e:
            log.warning(f"[WLANPi] get_country_code failed: {e}")
            return None

    def iw_scan_with_tx_power(self, interface: str = "wlan1") -> tuple[list[dict], str]:
        """
        Run a full `iw scan` on the WLANPi, parse TX power from the raw output,
        and return (networks_with_tx_power, raw_iw_output).

        The returned network dicts have the same shape as get_passive_scan()
        results but with 'ap_tx_dbm' populated where advertised.
        """
        try:
            # Trigger a fresh scan
            self.run(f"sudo /sbin/ip link set {interface} up 2>/dev/null || true")
            self.run(f"sudo /usr/sbin/iw dev {interface} scan trigger 2>/dev/null || true")
            time.sleep(3)
            raw, err = self.run(f"sudo /usr/sbin/iw dev {interface} scan dump")
            if not raw:
                log.warning(f"[WLANPi] iw scan dump returned empty output")
                return [], ""

            networks = _parse_iw_scan_output(raw)
            networks = enrich_networks_with_tx_power(networks, raw)
            log.info(f"[WLANPi] iw scan ({interface}): {len(networks)} networks, "
                     f"{sum(1 for n in networks if n.get('ap_tx_dbm') is not None)} with TX power")
            return networks, raw
        except Exception as e:
            log.warning(f"[WLANPi] iw_scan_with_tx_power failed: {e}")
            return [], ""


# ===========================================================================
# Wi-Fi Scanner — Windows (netsh)
# ===========================================================================

def _parse_netsh_networks(raw: str) -> list[dict]:
    """
    Parse `netsh wlan show networks mode=bssid` output into a list of dicts.
    Each dict represents one BSSID entry.
    """
    networks = []
    current_ssid = None
    current_bssid_block = {}

    for line in raw.splitlines():
        line = line.strip()

        ssid_match = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", line)
        if ssid_match:
            current_ssid = ssid_match.group(1).strip()
            continue

        bssid_match = re.match(r"^BSSID\s+\d+\s*:\s*(.+)$", line)
        if bssid_match:
            if current_bssid_block:
                networks.append(current_bssid_block)
            current_bssid_block = {
                "ssid": current_ssid or "",
                "bssid": bssid_match.group(1).strip().upper(),
                "signal": None,
                "channel": None,
                "band": None,
                "auth": None,
                "rssi": None,
            }
            continue

        if not current_bssid_block:
            continue

        signal_match = re.match(r"^Signal\s*:\s*(\d+)%$", line)
        if signal_match:
            pct = int(signal_match.group(1))
            # Convert Windows signal % to approximate RSSI (dBm)
            # Windows uses: RSSI = (signal% / 2) - 100
            rssi = (pct // 2) - 100
            current_bssid_block["signal"] = pct
            current_bssid_block["rssi"] = rssi
            continue

        channel_match = re.match(r"^Channel\s*:\s*(\d+)$", line)
        if channel_match:
            ch = int(channel_match.group(1))
            current_bssid_block["channel"] = ch
            current_bssid_block["band"] = "5 GHz" if ch > 14 else "2.4 GHz"
            continue

        auth_match = re.match(r"^Authentication\s*:\s*(.+)$", line)
        if auth_match:
            current_bssid_block["auth"] = auth_match.group(1).strip()
            continue

    if current_bssid_block:
        networks.append(current_bssid_block)

    return networks


def scan_networks_netsh(interface: str | None = None) -> list[dict]:
    """
    Run netsh scan and return parsed BSSID list.
    Pass interface to target a specific Wi-Fi adapter (e.g. "Wi-Fi 3").
    """
    try:
        cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
        if interface:
            cmd = ["netsh", "wlan", "show", "networks", f"interface={interface}", "mode=bssid"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        networks = _parse_netsh_networks(result.stdout)
        log.debug(f"[netsh] Found {len(networks)} networks.")
        return networks
    except subprocess.TimeoutExpired:
        log.warning("[netsh] Scan timed out")
        return []
    except Exception as e:
        log.warning(f"[netsh] Scan error: {e}")
        return []


def get_connected_ap_netsh() -> dict | None:
    """
    Returns info about the currently connected AP using netsh.
    Dict keys: ssid, bssid, channel, band, rssi, auth, tx_rate, rx_rate
    Returns None if not connected.
    """
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=8,
            encoding="utf-8",
            errors="replace",
        )
        raw = result.stdout
        info = {}

        patterns = {
            "ssid":    r"^\s+SSID\s*:\s*(.+)$",
            "bssid":   r"^\s+BSSID\s*:\s*(.+)$",
            "channel": r"^\s+Channel\s*:\s*(\d+)$",
            "rssi":    r"^\s+Signal\s*:\s*(\d+)%",
            "auth":    r"^\s+Authentication\s*:\s*(.+)$",
            "tx_rate": r"^\s+Transmit rate \(Mbps\)\s*:\s*(.+)$",
            "rx_rate": r"^\s+Receive rate \(Mbps\)\s*:\s*(.+)$",
            "state":   r"^\s+State\s*:\s*(.+)$",
        }

        for line in raw.splitlines():
            for key, pattern in patterns.items():
                m = re.match(pattern, line)
                if m and key not in info:
                    info[key] = m.group(1).strip()

        if info.get("state", "").lower() != "connected":
            return None

        if "bssid" in info:
            info["bssid"] = info["bssid"].upper()
        if "channel" in info:
            ch = int(info["channel"])
            info["channel"] = ch
            info["band"] = "5 GHz" if ch > 14 else "2.4 GHz"
        if "rssi" in info:
            pct = int(info["rssi"])
            info["rssi_pct"] = pct
            info["rssi"] = (pct // 2) - 100  # dBm estimate

        return info

    except Exception as e:
        log.warning(f"[netsh] Interface query error: {e}")
        return None


# ===========================================================================
# Wi-Fi Scanner — macOS (CoreWLAN)
# ===========================================================================

def _corewlan_channel_info(ch) -> tuple[int | None, str, int | None]:
    """
    Return (channel_num, band_label, freq_mhz) from a CWChannel object.

    CWChannelBand constants:
      0 = Unknown  1 = 2.4 GHz  2 = 5 GHz  3 = 6 GHz
    """
    if ch is None:
        return None, "2.4 GHz", None

    channel_num = int(ch.channelNumber())
    band_num    = int(ch.channelBand())

    if band_num == 3:                               # 6 GHz
        band     = "6 GHz"
        freq_mhz = 5950 + channel_num * 5
    elif band_num == 2 or channel_num > 14:         # 5 GHz
        band     = "5 GHz"
        freq_mhz = 5000 + channel_num * 5
    else:                                           # 2.4 GHz
        band     = "2.4 GHz"
        freq_mhz = 2412 + (channel_num - 1) * 5 if channel_num != 14 else 2484

    return channel_num, band, freq_mhz


def scan_networks_corewlan() -> list[dict]:
    """
    Scan for Wi-Fi networks using CoreWLAN on macOS.
    Returns a list of BSS dicts compatible with wifi_tool.py's cache layer.

    On macOS 14+ (Sonoma), SSIDs are only returned when the calling app has been
    granted Location Services permission.  When running as a bundled .app the OS
    will prompt for permission on first launch.  If permission is denied, networks
    are still returned but with blank SSIDs.
    """
    try:
        import objc  # noqa: F401
        from CoreWLAN import CWWiFiClient
    except ImportError:
        log.error("[CoreWLAN] CoreWLAN not available on this platform")
        return []

    try:
        client = CWWiFiClient.sharedWiFiClient()
        iface  = client.interface()
        if iface is None:
            log.warning("[CoreWLAN] No Wi-Fi interface found")
            return []

        # Ensure a CFRunLoop exists on this thread — required for CoreWLAN
        # API calls from non-main daemon threads in bundled .app contexts.
        try:
            import CoreFoundation
            CoreFoundation.CFRunLoopGetCurrent()
        except Exception:
            pass

        networks, error = iface.scanForNetworksWithName_error_(None, None)
        if error:
            log.warning(f"[CoreWLAN] Scan error: {error}")

        results = []
        for n in (networks or []):
            channel_num, band, freq_mhz = _corewlan_channel_info(n.wlanChannel())
            results.append({
                "ssid":          str(n.ssid() or ""),
                "bssid":         str(n.bssid() or "").upper(),
                "rssi":          int(n.rssiValue()),
                "channel":       channel_num,
                "band":          band,
                "freq_mhz":      freq_mhz,
                "auth":          str(n.security()) if hasattr(n, "security") else None,
                "signal":        None,
                "ch_util_pct":   None,
                "station_count": None,
            })

        blank = sum(1 for r in results if not r["ssid"])
        if blank:
            log.warning(
                f"[CoreWLAN] {blank}/{len(results)} networks have blank SSIDs. "
                "Location Services permission may be denied. "
                "Launch RF-DIAG as a .app bundle and grant access in "
                "System Settings > Privacy & Security > Location Services."
            )

        log.debug(f"[CoreWLAN] Found {len(results)} networks.")
        return results

    except Exception as e:
        log.warning(f"[CoreWLAN] Scan failed: {e}")
        return []


def get_connected_ap_corewlan() -> dict | None:
    """
    Returns info about the currently connected AP using CoreWLAN on macOS.
    """
    try:
        import objc  # noqa: F401
        from CoreWLAN import CWWiFiClient
        client = CWWiFiClient.sharedWiFiClient()
        iface  = client.interface()
        if iface is None:
            return None

        ssid  = iface.ssid()
        bssid = iface.bssid()
        if not ssid or not bssid:
            return None

        channel_num, band, freq_mhz = _corewlan_channel_info(iface.wlanChannel())

        return {
            "ssid":     str(ssid),
            "bssid":    str(bssid).upper(),
            "rssi":     int(iface.rssiValue()),
            "channel":  channel_num,
            "band":     band,
            "freq_mhz": freq_mhz,
            "tx_rate":  None,
            "rx_rate":  None,
        }
    except Exception as e:
        log.warning(f"[CoreWLAN] Connected AP query failed: {e}")
        return None


# ===========================================================================
# Platform dispatcher
# ===========================================================================

def scan_networks(netsh_interface: str | None = None) -> list[dict]:
    """Scan Wi-Fi networks — dispatches to the right backend."""
    if PLATFORM == "darwin":
        return scan_networks_corewlan()
    elif PLATFORM == "win32":
        return scan_networks_netsh(interface=netsh_interface)
    else:
        log.warning(f"[Scanner] Unsupported platform: {PLATFORM}")
        return []


def get_connected_ap() -> dict | None:
    """Get connected AP info — dispatches to the right backend."""
    if PLATFORM == "darwin":
        return get_connected_ap_corewlan()
    elif PLATFORM == "win32":
        return get_connected_ap_netsh()
    else:
        return None


# ===========================================================================
# Background scan thread with cache
# ===========================================================================

class ScanCache:
    """
    Runs a background thread that periodically scans for Wi-Fi networks
    and caches the results. Thread-safe reads via a lock.
    """

    def __init__(self, interval: int = 15, netsh_interface: str | None = None):
        self.interval = interval
        self.netsh_interface = netsh_interface
        self._lock = threading.Lock()
        self._networks: list[dict] = []
        self._connected_ap: dict | None = None
        self._last_scan: float = 0.0
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="wifi-scan-bg", daemon=True
        )
        self._thread.start()
        log.info(f"[ScanCache] Background scan started (interval={self.interval}s)")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        log.info("[ScanCache] Background scan stopped")

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                connected = get_connected_ap()
                with self._lock:
                    self._connected_ap = connected

                # Skip native scan when WLANPi is active — it has priority
                if wlanpi.reachable:
                    self._stop_event.wait(self.interval)
                    continue

                networks = scan_networks(netsh_interface=self.netsh_interface)
                with self._lock:
                    self._networks = networks
                    self._last_scan = time.time()
                log.debug(
                    f"[ScanCache] Refreshed: {len(networks)} networks, "
                    f"MBR: {connected.get('bssid') if connected else 'None'}"
                )
            except Exception as e:
                log.warning(f"[ScanCache] Scan error: {e}")

            self._stop_event.wait(self.interval)

    # ------------------------------------------------------------------
    # Read accessors (always safe to call from Flask routes)
    # ------------------------------------------------------------------

    @property
    def networks(self) -> list[dict]:
        with self._lock:
            return list(self._networks)

    @property
    def connected_ap(self) -> dict | None:
        with self._lock:
            return dict(self._connected_ap) if self._connected_ap else None

    @property
    def last_scan(self) -> float:
        with self._lock:
            return self._last_scan

    @property
    def last_scan_age(self) -> float:
        """Seconds since last successful scan."""
        t = self.last_scan
        return (time.time() - t) if t else float("inf")

    def snapshot(self) -> dict:
        """Return a JSON-serialisable snapshot of the current cache state."""
        connected = self.connected_ap
        return {
            "networks":     self.networks,
            "connected_ap": connected,
            "active_mbr":   connected.get("bssid") if connected else None,
            "last_scan_age_s": round(self.last_scan_age, 1),
            "platform":     PLATFORM,
        }


# ===========================================================================
# Module-level singletons  (import and use directly in wifi_tool.py)
# ===========================================================================

#: Shared WLANPi SSH connection
import os as _os
wlanpi = WLANPiSSH(
    host=None,  # Auto-detect: tries 169.254.42.1 (R4/Go) then 198.18.42.1
    user="wlanpi",
    password=_os.environ.get("WLANPI_PASSWORD"),
    key_path=_os.path.expanduser("~/.ssh/id_ed25519"),
)

#: Shared background scan cache (call .start() in wifi_tool.py after app init)
scan_cache = ScanCache(interval=15)


# ===========================================================================
# Cleanup hook (register in wifi_tool.py)
# ===========================================================================

def shutdown():
    """Call this on app shutdown to cleanly close threads and SSH."""
    scan_cache.stop()
    wlanpi.close()
    log.info("[wifi_utils] Shutdown complete")
