# ── Step 1: Add basic_rate_optimization function to wifi_utils.py ──
with open('wifi_utils.py', 'r') as f:
    c = f.read()

# Add the function before power_recommendation
basic_rate_func = '''
def basic_rate_optimization(ap_min_basic_rate=None, ap_basic_rates=None, ap_all_rates=None):
    """
    Analyse the AP\'s advertised minimum basic rate and return an optimization
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

'''

c = c.replace(
    'def power_recommendation(',
    basic_rate_func + 'def power_recommendation('
)

# Update analyse_network signature
c = c.replace(
    'def analyse_network(n: dict, active_mbr_mbps=None, ap_tx_dbm=None) -> dict:',
    'def analyse_network(n: dict, active_mbr_mbps=None, ap_tx_dbm=None,\n                    ap_min_basic_rate=None, ap_basic_rates=None, ap_all_rates=None) -> dict:'
)

# Add basic rate variables inside analyse_network
c = c.replace(
    '    tx      = ap_tx_dbm if ap_tx_dbm is not None else n.get("ap_tx_dbm")\n    return {',
    '''    tx      = ap_tx_dbm if ap_tx_dbm is not None else n.get("ap_tx_dbm")

    min_br  = ap_min_basic_rate if ap_min_basic_rate is not None else n.get("ap_min_basic_rate")
    br_list = ap_basic_rates    if ap_basic_rates    is not None else n.get("ap_basic_rates", [])
    all_r   = ap_all_rates      if ap_all_rates      is not None else n.get("ap_all_rates", [])

    return {'''
)

# Add basic_rate_opt to return dict
c = c.replace(
    '        "power":          power_recommendation(rssi, channel, ap_tx_dbm=tx),\n    }',
    '        "power":          power_recommendation(rssi, channel, ap_tx_dbm=tx),\n        "basic_rate_opt": basic_rate_optimization(min_br, br_list, all_r),\n    }'
)

with open('wifi_utils.py', 'w') as f:
    f.write(c)
print("wifi_utils.py updated!")

# ── Step 2: Add basic rate parsing to wifi_tool.py ──
with open('wifi_tool.py', 'r') as f:
    c = f.read()

# Add basic rate fields to network dict
c = c.replace(
    '                "ap_tx_dbm": None, "ch_util_pct": None, "station_count": None,',
    '                "ap_tx_dbm": None, "ch_util_pct": None, "station_count": None,\n                "ap_basic_rates": [], "ap_all_rates": [], "ap_min_basic_rate": None,'
)

# Add supported rates parsing after BSS Load section
old_bss = '        if re.match(r"BSS Load:", s, re.IGNORECASE):'
new_bss = '''        m = re.match(r"Supported rates:\\s*(.+)", s, re.IGNORECASE)
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

        m = re.match(r"Extended supported rates:\\s*(.+)", s, re.IGNORECASE)
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

        if re.match(r"BSS Load:", s, re.IGNORECASE):'''

c = c.replace(old_bss, new_bss)

# Add basic rate fields to CoreWLAN fallback
c = c.replace(
    '                "ap_tx_dbm":          None,\n                "ch_util_pct":        n.get("ch_util_pct"),\n                "station_count":      n.get("station_count"),',
    '                "ap_tx_dbm":          None,\n                "ch_util_pct":        n.get("ch_util_pct"),\n                "station_count":      n.get("station_count"),\n                "ap_basic_rates":     [],\n                "ap_all_rates":       [],\n                "ap_min_basic_rate":  None,'
)

# Update analyse_network call
c = c.replace(
    '            data = analyse_network(n, active_mbr_mbps=None,\n                                   ap_tx_dbm=n.get("ap_tx_dbm"))',
    '            data = analyse_network(n, active_mbr_mbps=None,\n                                   ap_tx_dbm=n.get("ap_tx_dbm"),\n                                   ap_min_basic_rate=n.get("ap_min_basic_rate"),\n                                   ap_basic_rates=n.get("ap_basic_rates", []),\n                                   ap_all_rates=n.get("ap_all_rates", []))'
)

with open('wifi_tool.py', 'w') as f:
    f.write(c)
print("wifi_tool.py updated!")
