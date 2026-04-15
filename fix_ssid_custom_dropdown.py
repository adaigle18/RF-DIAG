with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'r') as f:
    html = f.read()

# Fix 1 - Replace select CSS with custom dropdown CSS
html = html.replace(
    """  #ssid-filter {""",
    """  /* Custom SSID dropdown */
  .ssid-dropdown { position: relative; display: inline-block; }
  #ssid-filter-btn {
    font-family: var(--mono); font-size: 12px; cursor: pointer;
    background: var(--bg3); border: 1px solid var(--border);
    color: var(--text); padding: 4px 28px 4px 10px;
    min-width: 180px; text-align: left; position: relative;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  #ssid-filter-btn::after {
    content: '▾'; position: absolute; right: 8px; top: 50%;
    transform: translateY(-50%); color: var(--text-dim);
  }
  #ssid-filter-btn:focus { border-color: var(--green-dim); outline: none; }
  .ssid-drop-menu {
    display: none; position: absolute; top: 100%; left: 0; z-index: 300;
    background: var(--bg2); border: 1px solid var(--border);
    min-width: 220px; max-height: 260px; overflow-y: auto;
    margin-top: 2px;
  }
  .ssid-drop-menu.open { display: block; }
  .ssid-drop-item {
    padding: 7px 14px; font-size: 12px; cursor: pointer;
    color: var(--text); font-family: var(--mono);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .ssid-drop-item:hover { background: var(--bg3); color: var(--green); }
  .ssid-drop-item.selected { color: var(--green); }

  #ssid-filter {""",
)

# Fix 2 - Replace the select element with custom dropdown
html = html.replace(
    """  <select id="ssid-filter" onchange="renderTable()">
    <option value="">All SSIDs</option>
  </select>""",
    """  <div class="ssid-dropdown">
    <button id="ssid-filter-btn" onclick="toggleSsidMenu()">All SSIDs</button>
    <div class="ssid-drop-menu" id="ssid-drop-menu"></div>
  </div>
  <input type="hidden" id="ssid-filter" value="">"""
)

# Fix 3 - Replace the dropdown population JS
html = html.replace(
    """  // Populate SSID dropdown from scan results
  const ssidSelect = document.getElementById('ssid-filter');
  const currentVal = ssidSelect.value;
  const ssids = [...new Set(data.networks.map(n => n.ssid).filter(Boolean))].sort();
  ssidSelect.innerHTML = '<option value="">All SSIDs</option>' +
    ssids.map(s => `<option value="${s}" ${s === currentVal ? 'selected' : ''}>${s}</option>`).join('');""",
    """  // Populate custom SSID dropdown from scan results
  const currentVal = document.getElementById('ssid-filter').value;
  const ssids = [...new Set(data.networks.map(n => n.ssid).filter(Boolean))].sort();
  const menu = document.getElementById('ssid-drop-menu');
  menu.innerHTML = ['', ...ssids].map(s => `
    <div class="ssid-drop-item ${s === currentVal ? 'selected' : ''}"
         onclick="selectSsid('${s.replace(/'/g, "\\'")}')">
      ${s || 'All SSIDs'}
    </div>`).join('');"""
)

# Fix 4 - Add JS functions for custom dropdown
old_js = "  function toggleTheme() {"
new_js = """  // ── SSID custom dropdown ──
  function toggleSsidMenu() {
    document.getElementById('ssid-drop-menu').classList.toggle('open');
  }

  function selectSsid(val) {
    document.getElementById('ssid-filter').value = val;
    document.getElementById('ssid-filter-btn').textContent = val || 'All SSIDs';
    document.getElementById('ssid-drop-menu').classList.remove('open');
    // Update selected highlight
    document.querySelectorAll('.ssid-drop-item').forEach(el => {
      el.classList.toggle('selected', el.textContent.trim() === (val || 'All SSIDs'));
    });
    renderTable();
  }

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.ssid-dropdown')) {
      document.getElementById('ssid-drop-menu').classList.remove('open');
    }
  });

  function toggleTheme() {"""

html = html.replace(old_js, new_js)

with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'w') as f:
    f.write(html)

print("Done!")
