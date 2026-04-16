with open('templates/index.html', 'r') as f:
    html = f.read()

# Fix 1 - Add light theme CSS
html = html.replace(
    '  ::-webkit-scrollbar-thumb { background: var(--border); }',
    '''  ::-webkit-scrollbar-thumb { background: var(--border); }

  /* ── Light theme ── */
  body.light {
    --bg:        #f0f4f0;
    --bg2:       #e4eae4;
    --bg3:       #d8e0d8;
    --border:    #b0c8b0;
    --green:     #1a7a3a;
    --green2:    #1fcc57;
    --green-dim: #a8d8b8;
    --text:      #1a2e1a;
    --text-dim:  #4a6a4a;
    --text-mute: #7a9a7a;
  }

  /* ── Column toggle dropdown ── */
  .col-dropdown { position: relative; display: inline-block; }
  .col-menu {
    display: none; position: absolute; top: 100%; right: 0; z-index: 200;
    background: var(--bg2); border: 1px solid var(--border);
    min-width: 180px; padding: 8px 0; margin-top: 4px;
  }
  .col-menu.open { display: block; max-height: 300px; overflow-y: auto; }
  .col-menu label {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 14px; cursor: pointer; font-size: 11px;
    color: var(--text); text-transform: uppercase; letter-spacing: 1px;
  }
  .col-menu label:hover { background: var(--bg3); }
  .col-menu input[type=checkbox] { accent-color: var(--green); }

  /* ── Resizable columns ── */
  .net-table th { position: relative; }
  .col-resizer {
    position: absolute; right: 0; top: 0; bottom: 0;
    width: 5px; cursor: col-resize; background: transparent;
  }
  .col-resizer:hover { background: var(--green-dim); }

  /* ── Custom SSID dropdown ── */
  .ssid-dropdown { position: relative; display: inline-block; }
  #ssid-filter-btn {
    font-family: var(--mono); font-size: 12px; cursor: pointer;
    background: var(--bg3); border: 1px solid var(--border);
    color: var(--text); padding: 4px 28px 4px 10px;
    min-width: 180px; text-align: left; position: relative;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  #ssid-filter-btn::after {
    content: "▾"; position: absolute; right: 8px; top: 50%;
    transform: translateY(-50%); color: var(--text-dim);
  }
  #ssid-filter-btn:focus { border-color: var(--green-dim); outline: none; }
  .ssid-drop-menu {
    display: none; position: absolute; top: 100%; left: 0; z-index: 300;
    background: var(--bg2); border: 1px solid var(--border);
    min-width: 220px; max-height: 260px; overflow-y: auto; margin-top: 2px;
  }
  .ssid-drop-menu.open { display: block; }
  .ssid-drop-item {
    padding: 7px 14px; font-size: 12px; cursor: pointer;
    color: var(--text); font-family: var(--mono);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .ssid-drop-item:hover { background: var(--bg3); color: var(--green); }
  .ssid-drop-item.selected { color: var(--green); }'''
)

# Fix 2 - Add theme toggle button in header
html = html.replace(
    '    <button id="refresh-btn" class="btn" onclick="forceRefresh()">&#8635; Scan</button>',
    '    <button id="refresh-btn" class="btn" onclick="forceRefresh()">&#8635; Scan</button>\n    <button id="theme-toggle" class="btn" onclick="toggleTheme()" title="Toggle light/dark mode">&#9788; Light</button>'
)

# Fix 3 - Replace text SSID input with custom dropdown
html = html.replace(
    '  <input id="ssid-filter" type="text" placeholder="filter..." oninput="renderTable()">',
    '''  <div class="ssid-dropdown">
    <button id="ssid-filter-btn" onclick="toggleSsidMenu()">All SSIDs</button>
    <div class="ssid-drop-menu" id="ssid-drop-menu"></div>
  </div>
  <input type="hidden" id="ssid-filter" value="">'''
)

# Fix 4 - Add data-col attributes to th elements
html = html.replace(
    '<th class="sortable" data-sort="ssid"       onclick="setSort(\'ssid\')">SSID<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="ssid" data-col="ssid" onclick="setSort(\'ssid\')">SSID<span class="sort-arrow"></span></th>'
)
html = html.replace(
    '<th class="sortable" data-sort="bssid"      onclick="setSort(\'bssid\')">BSSID<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="bssid" data-col="bssid" onclick="setSort(\'bssid\')">BSSID<span class="sort-arrow"></span></th>'
)
html = html.replace(
    '<th class="sortable" data-sort="channel"    onclick="setSort(\'channel\')">Band / CH<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="channel" data-col="channel" onclick="setSort(\'channel\')">Band / CH<span class="sort-arrow"></span></th>'
)
html = html.replace(
    '<th class="sortable sort-desc" data-sort="rssi" onclick="setSort(\'rssi\')">RSSI<span class="sort-arrow"></span></th>',
    '<th class="sortable sort-desc" data-sort="rssi" data-col="rssi" onclick="setSort(\'rssi\')">RSSI<span class="sort-arrow"></span></th>'
)
html = html.replace(
    '<th class="sortable" data-sort="distance_m" onclick="setSort(\'distance_m\')">Distance (Pwr: 20dBm)<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="distance_m" data-col="distance" onclick="setSort(\'distance_m\')">Distance (Pwr: 20dBm)<span class="sort-arrow"></span></th>'
)
html = html.replace('<th>Band</th>', '<th data-col="band">Band</th>')
html = html.replace(
    '<th class="sortable" data-sort="mbr"        onclick="setSort(\'mbr\')">Min Basic Rate<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="mbr" data-col="mbr" onclick="setSort(\'mbr\')">Min Basic Rate<span class="sort-arrow"></span></th>'
)
html = html.replace('<th>TX Power</th>', '<th data-col="txpower">TX Power</th>')
html = html.replace(
    '<th class="sortable" data-sort="ch_util"    onclick="setSort(\'ch_util\')">CH Util<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="ch_util" data-col="chutil" onclick="setSort(\'ch_util\')">CH Util<span class="sort-arrow"></span></th>'
)
html = html.replace(
    '<th class="sortable" data-sort="ccc"        onclick="setSort(\'ccc\')">CCC<span class="sort-arrow"></span></th>',
    '<th class="sortable" data-sort="ccc" data-col="ccc" onclick="setSort(\'ccc\')">CCC<span class="sort-arrow"></span></th>'
)

# Fix 5 - Add Columns button above table
html = html.replace(
    '      <table class="net-table">',
    '''      <div style="display:flex;justify-content:flex-end;padding:8px 0 6px 0;">
        <div class="col-dropdown">
          <button class="btn" onclick="toggleColMenu()" id="col-menu-btn" style="border-color:var(--purple);color:var(--purple);">&#9638; Columns</button>
          <div class="col-menu" id="col-menu"></div>
        </div>
      </div>
      <table class="net-table">'''
)

# Fix 6 - Add data-col to td elements
html = html.replace(
    '      <td><strong>${n.ssid}</strong>${piBadge}${connBadge}</td>',
    '      <td data-col="ssid"><strong>${n.ssid}</strong>${piBadge}${connBadge}</td>'
)
html = html.replace(
    '      <td style="color:var(--text-dim);font-size:11px;">${n.bssid}</td>',
    '      <td data-col="bssid" style="color:var(--text-dim);font-size:11px;">${n.bssid}</td>'
)
html = html.replace(
    '      <td><span class="badge ${n.has_6ghz ? \'badge-6ghz\' : n.has_5ghz ? \'badge-blue\' : \'badge-warn\'}">${n.band}</span> &nbsp;<span style="color:var(--text-dim)">CH ${n.channel}</span></td>',
    '      <td data-col="channel"><span class="badge ${n.has_6ghz ? \'badge-6ghz\' : n.has_5ghz ? \'badge-blue\' : \'badge-warn\'}">${n.band}</span> &nbsp;<span style="color:var(--text-dim)">CH ${n.channel}</span></td>'
)
html = html.replace(
    '      <td><div class="rssi-bar-wrap">',
    '      <td data-col="rssi"><div class="rssi-bar-wrap">'
)
html = html.replace(
    '      <td>${n.distance_m} m <span style="color:var(--text-dim);font-size:10px;">(${n.distance_label})</span></td>',
    '      <td data-col="distance">${n.distance_m} m <span style="color:var(--text-dim);font-size:10px;">(${n.distance_label})</span></td>'
)
html = html.replace('      <td>${bandIndicator}</td>', '      <td data-col="band">${bandIndicator}</td>')
html = html.replace('      <td>${mbrSuppBadge}</td>', '      <td data-col="mbr">${mbrSuppBadge}</td>')
html = html.replace('      <td>${txBadge}</td>', '      <td data-col="txpower">${txBadge}</td>')
html = html.replace('      <td>${chUtilBadge}</td>', '      <td data-col="chutil">${chUtilBadge}</td>')
html = html.replace('      <td>${cccBadge}</td>', '      <td data-col="ccc">${cccBadge}</td>')

# Fix 7 - Update SSID filter logic
html = html.replace(
    "  const q = document.getElementById('ssid-filter').value.toLowerCase();",
    "  const selectedSsid = document.getElementById('ssid-filter').value;\n  const q = selectedSsid.toLowerCase();"
)

# Fix 8 - Populate SSID dropdown from scan results
html = html.replace(
    "    if (data.wlanpi_ssids && data.wlanpi_ssids.length) {",
    """    // Populate custom SSID dropdown
    const currentVal = document.getElementById('ssid-filter').value;
    const ssids = [...new Set(data.networks.map(n => n.ssid).filter(Boolean))].sort();
    const menu = document.getElementById('ssid-drop-menu');
    menu.innerHTML = ['', ...ssids].map(s => `
      <div class="ssid-drop-item ${s === currentVal ? 'selected' : ''}"
           onclick="selectSsid('${s.replace(/'/g, "\\'")}')">
        ${s || 'All SSIDs'}
      </div>`).join('');

    if (data.wlanpi_ssids && data.wlanpi_ssids.length) {"""
)

# Fix 9 - Add all JavaScript functions
html = html.replace(
    '// ═══════════════════════════════════════════════════════\n// MAIN DIAGNOSTIC LOGIC',
    '''  // ── Column definitions ──
  const COL_DEFS = [
    { id: "ssid",     label: "SSID" },
    { id: "bssid",    label: "BSSID" },
    { id: "channel",  label: "Band / CH" },
    { id: "rssi",     label: "RSSI" },
    { id: "distance", label: "Distance" },
    { id: "band",     label: "Band" },
    { id: "mbr",      label: "Min Basic Rate" },
    { id: "txpower",  label: "TX Power" },
    { id: "chutil",   label: "CH Util" },
    { id: "ccc",      label: "CCC" },
  ];

  let hiddenCols = new Set(JSON.parse(localStorage.getItem("hiddenCols") || "[]"));

  function buildColMenu() {
    const menu = document.getElementById("col-menu");
    menu.innerHTML = COL_DEFS.map(c => `
      <label>
        <input type="checkbox" ${!hiddenCols.has(c.id) ? "checked" : ""}
          onchange="toggleCol('${c.id}', this.checked)">
        ${c.label}
      </label>`).join("");
  }

  function toggleColMenu() {
    document.getElementById("col-menu").classList.toggle("open");
  }

  document.addEventListener("click", function(e) {
    if (!e.target.closest(".col-dropdown")) {
      document.getElementById("col-menu").classList.remove("open");
    }
    if (!e.target.closest(".ssid-dropdown")) {
      document.getElementById("ssid-drop-menu").classList.remove("open");
    }
  });

  function toggleCol(colId, visible) {
    if (visible) hiddenCols.delete(colId);
    else hiddenCols.add(colId);
    localStorage.setItem("hiddenCols", JSON.stringify([...hiddenCols]));
    applyColVisibility();
  }

  function applyColVisibility() {
    COL_DEFS.forEach(c => {
      const els = document.querySelectorAll(`[data-col="${c.id}"]`);
      els.forEach(el => el.style.display = hiddenCols.has(c.id) ? "none" : "");
    });
  }

  function initResizable() {
    const ths = document.querySelectorAll(".net-table th");
    ths.forEach(th => {
      const resizer = document.createElement("div");
      resizer.className = "col-resizer";
      th.appendChild(resizer);
      let startX, startW;
      resizer.addEventListener("mousedown", e => {
        startX = e.clientX; startW = th.offsetWidth;
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
        e.preventDefault();
      });
      function onMove(e) { th.style.width = (startW + e.clientX - startX) + "px"; }
      function onUp() {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      }
    });
  }

  function toggleSsidMenu() {
    document.getElementById("ssid-drop-menu").classList.toggle("open");
  }

  function selectSsid(val) {
    document.getElementById("ssid-filter").value = val;
    document.getElementById("ssid-filter-btn").textContent = val || "All SSIDs";
    document.getElementById("ssid-drop-menu").classList.remove("open");
    document.querySelectorAll(".ssid-drop-item").forEach(el => {
      el.classList.toggle("selected", el.textContent.trim() === (val || "All SSIDs"));
    });
    renderTable();
  }

  function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById("theme-toggle");
    if (body.classList.contains("light")) {
      body.classList.remove("light");
      btn.innerHTML = "&#9788; Light";
      localStorage.setItem("theme", "dark");
    } else {
      body.classList.add("light");
      btn.innerHTML = "&#9790; Dark";
      localStorage.setItem("theme", "light");
    }
  }
  if (localStorage.getItem("theme") === "light") {
    document.body.classList.add("light");
    document.getElementById("theme-toggle").innerHTML = "&#9790; Dark";
  }

  buildColMenu();
  applyColVisibility();
  window.addEventListener("load", initResizable);

// ═══════════════════════════════════════════════════════
// MAIN DIAGNOSTIC LOGIC'''
)

with open('templates/index.html', 'w') as f:
    f.write(html)
print("index.html UI fixes applied!")
