# Fix wifi_tool.py - auto-detect interface
with open('wifi_tool.py', 'r') as f:
    c = f.read()

c = c.replace(
    'WLANPI_SCAN_IFACE = "wlan0"   # WLANPi: wlan0=single adapter, wlan1/wlan2=multi',
    '''# Auto-detect WLANPi scan interface
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

WLANPI_SCAN_IFACE = "wlan1"   # WLANPi: wlan0=single adapter, wlan1/wlan2=multi'''
)

with open('wifi_tool.py', 'w') as f:
    f.write(c)
print("wifi_tool.py updated!")

# Fix wifi_utils.py - auto-detect IP
with open('wifi_utils.py', 'r') as f:
    c = f.read()

# Fix default host parameter
c = c.replace(
    '        host: str = "198.18.42.1",',
    '        host: str = None,'
)

# Fix self.host assignment to auto-detect
c = c.replace(
    '        self.host = host\n        self.user = user',
    '''        # Auto-detect WLANPi IP if not specified
        if host is None:
            import socket as _s
            for _ip in ["169.254.42.1", "198.18.42.1"]:
                try:
                    s = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect((_ip, 22))
                    s.close()
                    host = _ip
                    print(f"[WLANPi] Auto-detected host: {host}")
                    break
                except Exception:
                    pass
            if host is None:
                host = "169.254.42.1"  # default fallback
        self.host = host
        self.user = user'''
)

# Fix singleton instantiation
c = c.replace(
    'host="198.18.42.1",',
    'host=None,  # Auto-detect: tries 169.254.42.1 then 198.18.42.1'
)

with open('wifi_utils.py', 'w') as f:
    f.write(c)
print("wifi_utils.py updated!")
