import re

with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'r') as f:
    html = f.read()

# 1. Add CSS for column dropdown and resize handles
css = """
  /* ── Column toggle dropdown ── */
  .col-dropdown { position: relative; display: inline-block; }
  .col-menu {
    display: none; position: absolute; top: 100%; right: 0; z-index: 200;
    background: var(--bg2); border: 1px solid var(--border);
    min-width: 180px; padding: 8px 0; margin-top: 4px;
  }
  .col-menu.open { display: block; }
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
    width: 5px; cursor: col-resize;
    background: transparent;
  }
  .col-resizer:hover { background: var(--green-dim); }
"""
html = html.replace('</style>\n</head>', css + '</style>\n</head>', 1)

# 2. Add Columns button in filter bar
html = html.replace(
    '<div class="filter-bar">',
    '<div class="filter-bar">\n    <div class="col-dropdown">\n      <button class="btn" onclick="toggleColMenu()" id="col-menu-btn" style="border-color:var(--purple);color:var(--purple);">&#9638; Columns</button>\n      <div class="col-menu" id="col-menu"></div>\n    </div>'
)

# 3. Add data-col attributes to each th
cols = [
    ('data-sort="ssid"',       'data-col="ssid"'),
    ('data-sort="bssid"',      'data-col="bssid"'),
    ('data-sort="channel"',    'data-col="channel"'),
    ('data-sort="rssi"',       'data-col="rssi"'),
    ('data-sort="distance_m"', 'data-col="distance"'),
    ('<th>Band</th>',           '<th data-col="band">Band</th>'),
    ('data-sort="mbr"',        'data-col="mbr"'),
    ('<th>TX Power</th>',       '<th data-col="txpower">TX Power</th>'),
    ('data-sort="ch_util"',    'data-col="chutil"'),
    ('data-sort="ccc"',        'data-col="ccc"'),
]
for old, new in cols:
    html = html.replace(old, old + ' ' + new if '<th>' not in old else new, 1)

# 4. Add resizer divs to th elements
html = re.sub(
    r'(<th[^>]*>)(.*?)(<span class="sort-arrow"></span></th>)',
    r'\1\2\3',
    html
)

# 5. Add JavaScript after <script> tag
js = """
  // ── Column definitions ──
  const COL_DEFS = [
    { id: 'ssid',     label: 'SSID' },
    { id: 'bssid',    label: 'BSSID' },
    { id: 'channel',  label: 'Band / CH' },
    { id: 'rssi',     label: 'RSSI' },
    { id: 'distance', label: 'Distance' },
    { id: 'band',     label: 'Band' },
    { id: 'mbr',      label: 'MBR Supported' },
    { id: 'txpower',  label: 'TX Power' },
    { id: 'chutil',   label: 'CH Util' },
    { id: 'ccc',      label: 'CCC' },
  ];

  let hiddenCols = new Set(JSON.parse(localStorage.getItem('hiddenCols') || '[]'));

  function buildColMenu() {
    const menu = document.getElementById('col-menu');
    menu.innerHTML = COL_DEFS.map(c => `
      <label>
        <input type="checkbox" ${!hiddenCols.has(c.id) ? 'checked' : ''}
          onchange="toggleCol('${c.id}', this.checked)">
        ${c.label}
      </label>`).join('');
  }

  function toggleColMenu() {
    document.getElementById('col-menu').classList.toggle('open');
  }

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.col-dropdown')) {
      document.getElementById('col-menu').classList.remove('open');
    }
  });

  function toggleCol(colId, visible) {
    if (visible) hiddenCols.delete(colId);
    else hiddenCols.add(colId);
    localStorage.setItem('hiddenCols', JSON.stringify([...hiddenCols]));
    applyColVisibility();
  }

  function applyColVisibility() {
    COL_DEFS.forEach(c => {
      const els = document.querySelectorAll(`[data-col="${c.id}"]`);
      els.forEach(el => el.style.display = hiddenCols.has(c.id) ? 'none' : '');
    });
  }

  // ── Resizable columns ──
  function initResizable() {
    const ths = document.querySelectorAll('.net-table th');
    ths.forEach(th => {
      const resizer = document.createElement('div');
      resizer.className = 'col-resizer';
      th.appendChild(resizer);
      let startX, startW;
      resizer.addEventListener('mousedown', e => {
        startX = e.clientX;
        startW = th.offsetWidth;
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
        e.preventDefault();
      });
      function onMove(e) { th.style.width = (startW + e.clientX - startX) + 'px'; }
      function onUp()    { document.removeEventListener('mousemove', onMove);
                           document.removeEventListener('mouseup', onUp); }
    });
  }

  buildColMenu();
  applyColVisibility();
  window.addEventListener('load', initResizable);
"""
html = html.replace('<script>\n  function toggleTheme', '<script>\n' + js + '\n  function toggleTheme', 1)

with open('/Users/mariomarcheggiani/RF-DIAG/templates/index.html', 'w') as f:
    f.write(html)

print("Done!")
