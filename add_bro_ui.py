with open('templates/index.html', 'r') as f:
    html = f.read()

# Step 1 - Add CSS for BRO
html = html.replace(
    '  .mbr-mismatch-box { font-size: 10px; padding: 6px 10px; border-left: 2px solid var(--amber); color: var(--amber); background: #1a1000; margin-top: 6px; line-height: 1.5; }',
    '''  .mbr-mismatch-box { font-size: 10px; padding: 6px 10px; border-left: 2px solid var(--amber); color: var(--amber); background: #1a1000; margin-top: 6px; line-height: 1.5; }

  .br-opt-box { font-size: 10px; padding: 8px 10px; margin-top: 8px; border-left: 3px solid; line-height: 1.6; }
  .br-opt-box.good   { border-color: var(--green); color: var(--green); background: #001a08; }
  .br-opt-box.warn   { border-color: var(--amber); color: var(--amber); background: #1a1000; }
  .br-opt-box.danger { border-color: var(--red);   color: var(--red);   background: #1a0000; }
  .br-opt-box.unknown{ border-color: var(--text-dim); color: var(--text-dim); background: var(--bg3); }
  .br-rate-pill { display: inline-block; font-size: 9px; padding: 1px 5px; border-radius: 3px; margin: 1px; background: var(--bg2); border: 1px solid var(--border); color: var(--text-dim); }
  .br-rate-pill.basic { border-color: var(--green-dim); color: var(--green); }
  .br-rate-pill.basic.legacy { border-color: var(--red); color: var(--red); }
  .br-opt-warn-icon { color: var(--amber); font-size: 9px; margin-left: 3px; cursor: help; }
  .no-wlanpi-tip { font-size: 10px; padding: 7px 10px; margin-top: 8px; border-left: 2px solid var(--text-mute); color: var(--text-dim); background: var(--bg2); line-height: 1.6; }'''
)

# Step 2 - Update MBR badge to show basic rate
html = html.replace(
    '''    const mbrSuppBadge = n.mbr.best_supported
      ? `<span class="badge badge-good">${n.mbr.best_supported} Mbps</span>`
      : `<span class="badge badge-danger">Marginal</span>`;''',
    '''    const bro = n.basic_rate_opt || {};
    let mbrSuppBadge;
    if (bro.min_basic_rate !== null && bro.min_basic_rate !== undefined) {
      const cls = bro.severity === "good" ? "badge-good" : bro.severity === "danger" ? "badge-danger" : "badge-warn";
      const warn = bro.needs_change ? `<span class="br-opt-warn-icon" title="${bro.advice}">&#9650;</span>` : "";
      mbrSuppBadge = `<span class="badge ${cls}">${bro.min_basic_rate} Mbps</span>${warn}`;
    } else if (n.mbr.best_supported) {
      mbrSuppBadge = `<span class="badge badge-dim">${n.mbr.best_supported} Mbps</span>`;
    } else {
      mbrSuppBadge = `<span class="badge badge-danger">Marginal</span>`;
    }'''
)

# Step 3 - Replace MBR detail section with Basic Rate Optimization
html = html.replace(
    '''      <div class="detail-section">
        <h4>MBR - Supported vs Active</h4>
        <div class="mbr-compare">
          <div class="mbr-row"><span class="mbr-label">Supported (RSSI)</span><span>${suppRates}</span></div>
          <div class="mbr-row"><span class="mbr-label">Active (WLANPi)</span><span>${activeMbrHtml}</span></div>
        </div>
        ${mismatchHtml}''',
    '''      <div class="detail-section">
        <h4>Basic Rate Optimization</h4>
        ${(() => {
          const bro = n.basic_rate_opt || {};
          const sev = bro.severity || "unknown";
          const allR = bro.all_rates || [];
          const basicR = new Set(bro.basic_rates || []);
          const legacyCCK = new Set([1, 2, 5.5, 11]);
          const pillsHtml = allR.length
            ? allR.map(r => {
                const isBasic = basicR.has(r);
                const isLegacy = isBasic && legacyCCK.has(r);
                const cls = isBasic ? (isLegacy ? "basic legacy" : "basic") : "";
                return `<span class="br-rate-pill ${cls}" title="${isBasic ? "Basic rate" : "Supported rate"}">${r}</span>`;
              }).join("")
            : "";
          const minBrHtml = bro.min_basic_rate !== null && bro.min_basic_rate !== undefined
            ? `<span class="badge ${sev==="good"?"badge-good":sev==="danger"?"badge-danger":"badge-warn"}">${bro.min_basic_rate} Mbps</span>`
            : `<span class="badge badge-dim">N/A</span>`;
          const recHtml = bro.recommended_min
            ? `<div class="kv"><span class="k">Recommended min</span><span class="v" style="color:var(--green);">12 Mbps</span></div>`
            : `<div class="kv"><span class="k">Recommended min</span><span class="v good">Already optimal</span></div>`;
          const BR_THR = { 6: -82, 12: -79, 24: -74 };
          let coverageHtml = "";
          if (bro.needs_change && bro.recommended_min) {
            const thr = BR_THR[bro.recommended_min] ?? -79;
            const rssiOk = n.rssi >= thr;
            coverageHtml = rssiOk
              ? `<div class="br-opt-box good">&#10003; RSSI ${n.rssi} dBm — sufficient for ${bro.recommended_min} Mbps (threshold ${thr} dBm).</div>`
              : `<div class="br-opt-box warn">&#9888; RSSI ${n.rssi} dBm — below threshold ${thr} dBm for ${bro.recommended_min} Mbps. Check from a more central location first.</div>`;
          }
          const noWlanpiTip = !allR.length
            ? `<div class="no-wlanpi-tip">Basic rates not available without WLANPi.</div>`
            : "";
          return `
          <div class="detail-kv">
            <div class="kv"><span class="k">AP Min Basic Rate</span><span>${minBrHtml}</span></div>
            ${recHtml}
          </div>
          ${allR.length ? `<div style="margin:8px 0 4px;font-size:10px;color:var(--text-mute);text-transform:uppercase;letter-spacing:1px;">Rates (highlighted = basic)</div>
          <div style="margin-bottom:6px;">${pillsHtml}</div>` : ""}
          <div class="br-opt-box ${sev}">${bro.advice || "No data."}</div>
          ${coverageHtml}
          ${noWlanpiTip}`;
        })()}'''
)

with open('templates/index.html', 'w') as f:
    f.write(html)
print("index.html updated!")
