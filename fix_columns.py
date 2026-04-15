with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'r') as f:
    html = f.read()

# Fix 1 - Add max-height and scroll to dropdown menu
html = html.replace(
    '  .col-menu.open { display: block; }',
    '  .col-menu.open { display: block; max-height: 300px; overflow-y: auto; }'
)

# Fix 2 - Add data-col to each <td> in tr.innerHTML
old_tr = """      <td><strong>${n.ssid}</strong>${piBadge}${connBadge}</td>
      <td style="color:var(--text-dim);font-size:11px;">${n.bssid}</td>
      <td><span class="badge ${n.has_6ghz ? 'badge-6ghz' : n.has_5ghz ? 'badge-blue' : 'badge-warn'}">${n.band}</span> &nbsp;<span style="color:var(--text-dim)">CH ${n.channel}</span></td>
      <td><div class="rssi-bar-wrap">
        <div class="rssi-bar"><div class="rssi-fill" style="width:${pct}%;background:${color};"></div></div>
        <span style="color:${color};font-weight:500;">${n.rssi} dBm</span>
      </div></td>
      <td>${n.distance_m} m <span style="color:var(--text-dim);font-size:10px;">(${n.distance_label})</span></td>
      <td>${bandIndicator}</td>
      <td>${mbrSuppBadge}</td>
      <td>${txBadge}</td>
      <td>${chUtilBadge}</td>
      <td>${cccBadge}</td>"""

new_tr = """      <td data-col="ssid"><strong>${n.ssid}</strong>${piBadge}${connBadge}</td>
      <td data-col="bssid" style="color:var(--text-dim);font-size:11px;">${n.bssid}</td>
      <td data-col="channel"><span class="badge ${n.has_6ghz ? 'badge-6ghz' : n.has_5ghz ? 'badge-blue' : 'badge-warn'}">${n.band}</span> &nbsp;<span style="color:var(--text-dim)">CH ${n.channel}</span></td>
      <td data-col="rssi"><div class="rssi-bar-wrap">
        <div class="rssi-bar"><div class="rssi-fill" style="width:${pct}%;background:${color};"></div></div>
        <span style="color:${color};font-weight:500;">${n.rssi} dBm</span>
      </div></td>
      <td data-col="distance">${n.distance_m} m <span style="color:var(--text-dim);font-size:10px;">(${n.distance_label})</span></td>
      <td data-col="band">${bandIndicator}</td>
      <td data-col="mbr">${mbrSuppBadge}</td>
      <td data-col="txpower">${txBadge}</td>
      <td data-col="chutil">${chUtilBadge}</td>
      <td data-col="ccc">${cccBadge}</td>"""

html = html.replace(old_tr, new_tr)

# Fix 3 - Move Columns button - remove from filter bar
html = html.replace(
    '<div class="filter-bar">\n    <div class="col-dropdown">\n      <button class="btn" onclick="toggleColMenu()" id="col-menu-btn" style="border-color:var(--purple);color:var(--purple);">&#9638; Columns</button>\n      <div class="col-menu" id="col-menu"></div>\n    </div>',
    '<div class="filter-bar">'
)

# Fix 3 - Add Columns button in a new toolbar above the table
old_table = '      <table class="net-table">'
new_table = """      <div style="display:flex;justify-content:flex-end;padding:8px 0 6px 0;">
        <div class="col-dropdown">
          <button class="btn" onclick="toggleColMenu()" id="col-menu-btn" style="border-color:var(--purple);color:var(--purple);">&#9638; Columns</button>
          <div class="col-menu" id="col-menu"></div>
        </div>
      </div>
      <table class="net-table">"""

html = html.replace(old_table, new_table)

with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'w') as f:
    f.write(html)

print("Done!")
