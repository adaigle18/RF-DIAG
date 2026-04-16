with open('/Users/mariomarcheggiani/RF-DIAG/wifi_tool.py', 'r') as f:
    html = f.read()

html = html.replace(
    """    print(f"Platform: {sys.platform}")
    print(f"WLANPi scan interface: {WLANPI_SCAN_IFACE}")
    print("Running initial scan...")
    time.sleep(10)
    refresh_cache()""",
    """    # Start prober first so WLANPi is detected before initial scan
    threading.Thread(target=wlanpi_prober, daemon=True).start()

    print(f"Platform: {sys.platform}")
    print(f"WLANPi scan interface: {WLANPI_SCAN_IFACE}")
    print("Running initial scan...")
    time.sleep(10)
    refresh_cache()"""
)

html = html.replace(
    """    threading.Thread(target=background_refresher, daemon=True).start()
    threading.Thread(target=wlanpi_prober, daemon=True).start()""",
    """    threading.Thread(target=background_refresher, daemon=True).start()"""
)

with open('/Users/mariomarcheggiani/RF-DIAG/wifi_tool.py', 'w') as f:
    f.write(html)

print("Done!")
