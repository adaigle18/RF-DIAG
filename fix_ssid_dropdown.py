with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'r') as f:
    html = f.read()

# Fix 1 - Replace the text input CSS with dropdown CSS
html = html.replace(
    '  #ssid-filter {\n',
    '  #ssid-filter {\n'
)

old_css = """  #ssid-filter {"""
new_css = """  #ssid-filter {"""
# Leave CSS mostly as-is, just add select styling
html = html.replace(
    '  #ssid-filter:focus { border-color: var(--green-dim); }',
    """  #ssid-filter:focus { border-color: var(--green-dim); }
  #ssid-filter option {
    background: var(--bg2); color: var(--text);
    font-family: var(--mono); font-size: 12px;
  }"""
)

# Fix 2 - Replace the text input with a select dropdown
html = html.replace(
    '  <input id="ssid-filter" type="text" placeholder="filter..." oninput="renderTable()">',
    """  <select id="ssid-filter" onchange="renderTable()">
    <option value="">All SSIDs</option>
  </select>"""
)

# Fix 3 - Replace the filter logic in renderTable
html = html.replace(
    '  const q = document.getElementById(\'ssid-filter\').value.toLowerCase();',
    '  const q = document.getElementById(\'ssid-filter\').value.toLowerCase();'
)

# Fix 4 - Update the SSID filter logic to work with exact match from dropdown
html = html.replace(
    "  const q = document.getElementById('ssid-filter').value.toLowerCase();",
    """  const selectedSsid = document.getElementById('ssid-filter').value;
  const q = selectedSsid.toLowerCase();"""
)

# Fix 5 - Add function to populate SSID dropdown from scan data
old_update = "  if (data.wlanpi_ssids && data.wlanpi_ssids.length) {"
new_update = """  // Populate SSID dropdown from scan results
  const ssidSelect = document.getElementById('ssid-filter');
  const currentVal = ssidSelect.value;
  const ssids = [...new Set(data.networks.map(n => n.ssid).filter(Boolean))].sort();
  ssidSelect.innerHTML = '<option value="">All SSIDs</option>' +
    ssids.map(s => `<option value="${s}" ${s === currentVal ? 'selected' : ''}>${s}</option>`).join('');

  if (data.wlanpi_ssids && data.wlanpi_ssids.length) {"""

html = html.replace(old_update, new_update)

with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'w') as f:
    f.write(html)

print("Done!")
