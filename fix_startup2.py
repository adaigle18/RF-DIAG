with open('/Users/mariomarcheggiani/RF-DIAG/wifi_tool.py', 'r') as f:
    content = f.read()

content = content.replace(
    """    # Start prober first so WLANPi is detected before initial scan
    threading.Thread(target=wlanpi_prober, daemon=True).start()

    print(f"Platform: {sys.platform}")
    print(f"WLANPi scan interface: {WLANPI_SCAN_IFACE}")
    print("Running initial scan...")
    time.sleep(10)
    refresh_cache()

    n   = len(_cache["networks"])
    src = _cache["scan_source"]
    print(f"Found {n} networks via {src}.")
    print("WLANPi: not connected / unavailable" if not wlanpi.available else f"WLANPi OK [{WLANPI_SCAN_IFACE}]")

    threading.Thread(target=background_refresher, daemon=True).start()""",
    """    print(f"Platform: {sys.platform}")
    print(f"WLANPi scan interface: {WLANPI_SCAN_IFACE}")

    # Start prober first — it will trigger initial scan when WLANPi detected
    threading.Thread(target=wlanpi_prober, daemon=True).start()
    threading.Thread(target=background_refresher, daemon=True).start()

    print("Waiting for WLANPi detection...")
    time.sleep(12)

    n   = len(_cache["networks"])
    src = _cache["scan_source"]
    print(f"Found {n} networks via {src}.")
    print("WLANPi: not connected / unavailable" if not wlanpi.available else f"WLANPi OK [{WLANPI_SCAN_IFACE}]")"""
)

with open('/Users/mariomarcheggiani/RF-DIAG/wifi_tool.py', 'w') as f:
    f.write(content)

print("Done!")
