let allCases = [];
let selectedCaseId = "HHG-001";
let currentFilter = "all";
let cyInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchCases();
  setupEventListeners();
});

function setupEventListeners() {
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      currentFilter = e.target.getAttribute("data-filter");
      renderCaseList();
    });
  });

  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderCaseList();
    });
  }
}

async function fetchCases() {
  try {
    const res = await fetch("/api/cases");
    if (!res.ok) throw new Error("Failed to load cases");
    allCases = await res.json();
    renderStats();
    renderCaseList();
    if (allCases.length > 0) {
      selectCase(allCases[0].case_id);
    }
  } catch (err) {
    console.error("Error fetching cases:", err);
    document.getElementById("caseListBody").innerHTML = `
      <tr><td colspan="5" style="text-align:center; padding: 2rem; color: #dc2626;">
        Failed to load cases from server: ${err.message}
      </td></tr>
    `;
  }
}

function renderStats() {
  const total = allCases.length;
  const resolved = allCases.filter(c => ["fraud", "legitimate"].includes(c.case?.verdict)).length;
  const escalated = allCases.filter(c => c.case?.verdict === "uncertain" || c.case?.status === "escalated").length;
  const sars = allCases.filter(c => c.sar?.file === true).length;
  const syncCount = allCases.filter(c => c.case?.written_to_graph === true).length;

  document.getElementById("statTotal").innerText = total;
  document.getElementById("statResolved").innerText = resolved;
  document.getElementById("statEscalated").innerText = escalated;
  document.getElementById("statSars").innerText = sars;
  document.getElementById("statSync").innerText = `${syncCount}/${total}`;
}

function getStatusBadge(status, verdict) {
  if (status === "closed_legitimate" || verdict === "legitimate") {
    return `<span class="badge badge-legitimate">● legitimate</span>`;
  }
  if (status === "closed_fraud" || verdict === "fraud") {
    return `<span class="badge badge-fraud">● closed_fraud</span>`;
  }
  return `<span class="badge badge-escalated">● escalated</span>`;
}

function renderCaseList() {
  const tbody = document.getElementById("caseListBody");
  const query = (document.getElementById("searchInput")?.value || "").toLowerCase();

  const filtered = allCases.filter(item => {
    const status = item.case?.status || "";
    const verdict = item.case?.verdict || "";
    const pattern = (item.case?.pattern || "").toLowerCase();
    const caseId = (item.case_id || "").toLowerCase();

    // Filter by tab
    if (currentFilter === "escalated" && !(status === "escalated" || verdict === "uncertain")) return false;
    if (currentFilter === "fraud" && !(status === "closed_fraud" || verdict === "fraud")) return false;
    if (currentFilter === "legitimate" && !(status === "closed_legitimate" || verdict === "legitimate")) return false;

    // Filter by search query
    if (query) {
      return caseId.includes(query) || pattern.includes(query) || status.includes(query) || verdict.includes(query);
    }
    return true;
  });

  document.getElementById("filteredCount").innerText = `${filtered.length} of ${allCases.length}`;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: #64748b;">No cases match criteria</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(item => {
    const c = item.case || {};
    const isSelected = item.case_id === selectedCaseId;
    const badge = getStatusBadge(c.status, c.verdict);
    const sarBadge = item.sar?.file ? `<span class="sar-tag-yes">FILE SAR</span>` : `<span class="sar-tag-no">None</span>`;
    const prob = c.fraud_probability !== undefined ? `${Math.round(c.fraud_probability * 100)}%` : "N/A";

    return `
      <tr class="case-row ${isSelected ? 'selected' : ''}" onclick="selectCase('${item.case_id}')">
        <td class="case-id-cell">${item.case_id}</td>
        <td><span class="pattern-tag">${c.pattern || 'none'}</span></td>
        <td>${badge}</td>
        <td style="font-weight:600; color:#0f172a;">${prob}</td>
        <td>${sarBadge}</td>
      </tr>
    `;
  }).join("");
}

function selectCase(caseId) {
  selectedCaseId = caseId;
  renderCaseList();

  const item = allCases.find(c => c.case_id === caseId);
  if (!item) return;

  renderCaseDetail(item);
}

function renderCaseDetail(data) {
  const container = document.getElementById("caseDetailContainer");
  const c = data.case || {};
  const sar = data.sar || {};
  const actions = data.next_best_actions || {};
  const initialActions = actions.initial || [];
  const finalActions = actions.final || [];
  const whatChanged = actions.what_changed || "nothing";
  const evidence = c.evidence || [];
  const simCases = c.similar_prior_cases || [];

  const isEscalated = c.status === "escalated" || c.verdict === "uncertain";
  const isFraud = c.status === "closed_fraud" || c.verdict === "fraud";
  const isLegit = c.status === "closed_legitimate" || c.verdict === "legitimate";

  const probColor = isFraud ? "#dc2626" : (isLegit ? "#16a34a" : "#d97706");
  const badgeHtml = getStatusBadge(c.status, c.verdict);

  // Extract transaction info
  let txnId = c.affected_txn_ids?.[0] || c.first_suspicious_txn_id || "N/A";
  let cardId = c.connected_card_ids?.[0] || "N/A";
  let deviceProfile = c.connected_device_profiles?.[0] || null;
  let exposure = c.exposure_usd !== undefined ? `$${c.exposure_usd.toFixed(2)}` : "$0.00";

  // Extract customer ID
  let custId = "N/A";
  const custEv = evidence.find(e => e.ref === "get_customer_history");
  if (custEv && custEv.entity_ids && custEv.entity_ids.length > 0) {
    custId = custEv.entity_ids[0];
  } else if (cardId && cardId.includes("-")) {
    custId = cardId.split("-")[0];
  }

  // Extract billing region
  let regionId = "Region 444.0";
  const allText = (c.summary || "") + " " + evidence.map(e => e.claim).join(" ") + " " + (data.trigger_text || "");
  const regMatch = allText.match(/billing region ([0-9.]+)|region ([0-9.]+)/i);
  if (regMatch) {
    regionId = `Region ${regMatch[1] || regMatch[2]}`;
  }

  container.innerHTML = `
    <div class="detail-content">
      
      <!-- Top Banner -->
      <div class="case-banner">
        <div class="banner-left">
          <h2>
            <span>${data.case_id}</span>
            ${badgeHtml}
          </h2>
          <div class="banner-meta">
            <span class="banner-meta-item">Pattern: <strong>${c.pattern || 'none'}</strong></span>
            <span class="banner-meta-item">Txn: <strong>#${txnId}</strong></span>
            <span class="banner-meta-item">Customer: <strong>${custId}</strong></span>
            <span class="banner-meta-item">Card: <strong>${cardId}</strong></span>
            <span class="banner-meta-item">Exposure: <strong>${exposure}</strong></span>
          </div>
        </div>
        <div class="banner-right">
          <div class="prob-gauge">
            <div class="prob-number" style="color: ${probColor}">
              ${c.fraud_probability !== undefined ? Math.round(c.fraud_probability * 100) : 50}%
            </div>
            <div class="prob-label">Assessed Probability</div>
          </div>
          <div class="graph-sync-tag">
            <span>✓</span> Synced with TigerGraph
          </div>
        </div>
      </div>

      <!-- Graph Visualization Panel (Cytoscape.js) -->
      <div class="graph-viz-panel">
        <div class="graph-header-row">
          <div class="graph-title">
            <span>🕸️ Knowledge Graph Subgraph Topology</span>
          </div>
          <div class="graph-controls">
            <button class="graph-btn" onclick="fitGraph()">Fit</button>
            <button class="graph-btn" onclick="zoomInGraph()">Zoom +</button>
            <button class="graph-btn" onclick="zoomOutGraph()">Zoom &minus;</button>
            <button class="graph-btn" onclick="resetGraph()">Reset</button>
          </div>
        </div>

        <!-- Cytoscape Container -->
        <div id="cy"></div>

        <!-- Node Attributes Inspector Drawer -->
        <div id="nodeDetailsDrawer" class="node-details-drawer">
          <span style="font-weight:600; color:#0f172a;">Interactive Inspector:</span>
          <span style="color:#64748b; margin-left: 0.5rem;">Click any vertex in the subgraph above to inspect connected attributes, claims, and relations.</span>
        </div>

        <!-- Vertex Legend -->
        <div class="graph-legend">
          <div class="legend-item"><div class="legend-dot" style="background:#ea580c;"></div> Transaction (Flagged)</div>
          <div class="legend-item"><div class="legend-dot" style="background:#4f46e5;"></div> Customer</div>
          <div class="legend-item"><div class="legend-dot" style="background:#0284c7;"></div> Card</div>
          <div class="legend-item"><div class="legend-dot" style="background:#9333ea;"></div> DeviceProfile</div>
          <div class="legend-item"><div class="legend-dot" style="background:#0d9488;"></div> BillingRegion</div>
          <div class="legend-item"><div class="legend-dot" style="background:#e11d48;"></div> Similar FraudCase</div>
        </div>
      </div>

      <!-- Pipeline Flowchart -->
      <div class="pipeline-flow">
        <div class="flow-title">Investigation Execution Chain</div>
        <div class="flow-steps">
          <div class="flow-step active">
            <div class="flow-step-num">Step 1</div>
            <div class="flow-step-name">7 Graph Queries</div>
          </div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-step active">
            <div class="flow-step-num">Step 2</div>
            <div class="flow-step-name">Policy RAG Grounding</div>
          </div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-step active">
            <div class="flow-step-num">Step 3</div>
            <div class="flow-step-name">Uncertainty Assessment</div>
          </div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-step ${isEscalated ? 'pending' : 'active'}">
            <div class="flow-step-num">Step 4</div>
            <div class="flow-step-name">${isEscalated ? 'Evidence Hold' : 'Stoppage Criteria Met'}</div>
          </div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-step ${isFraud && sar.file ? 'active' : ''}">
            <div class="flow-step-num">Step 5</div>
            <div class="flow-step-name">${sar.file ? 'SAR Filing Mandated' : 'Provisional Case State'}</div>
          </div>
        </div>
      </div>

      <!-- Side-by-Side Next Best Actions -->
      <div class="detail-section">
        <div class="section-title">
          <span>⚡ Next Best Actions &mdash; Initial vs Final Distinction</span>
        </div>
        <div class="actions-comparison-grid">
          
          <!-- Initial Actions -->
          <div class="action-card-col">
            <div class="col-header">
              <span>1. Initial Actions (Pre-Evidence)</span>
              <span style="font-size:0.68rem; color:#64748b;">Stage 1 Gate</span>
            </div>
            <div class="action-items-list">
              ${initialActions.map(act => `
                <div class="action-item">
                  <div class="action-title-row">
                    <span class="action-name">${act.action}</span>
                    <span class="route-tag">${act.route || 'auto'}</span>
                  </div>
                  <div class="action-reason">${act.reason || ''}</div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Final Actions -->
          <div class="action-card-col">
            <div class="col-header">
              <span>2. Final Actions (Post-Evaluation)</span>
              <span style="font-size:0.68rem; color:${isEscalated ? '#b45309' : '#15803d'}; font-weight:700;">
                ${isEscalated ? 'Pending External Evidence' : 'Final Disposition'}
              </span>
            </div>
            <div class="action-items-list">
              ${finalActions.map(act => `
                <div class="action-item">
                  <div class="action-title-row">
                    <span class="action-name">${act.action}</span>
                    <span class="route-tag">${act.route || 'auto'}</span>
                  </div>
                  <div class="action-reason">${act.reason || ''}</div>
                </div>
              `).join('')}
            </div>
            <div class="what-changed-box">
              <strong>Transition Rationale:</strong> ${whatChanged}
            </div>
          </div>

        </div>
      </div>

      <!-- Evidence Grounding -->
      <div class="detail-section">
        <div class="section-title">
          <span>🔍 TigerGraph Graph Evidence Items (${evidence.length})</span>
        </div>
        <div class="evidence-list">
          ${evidence.map(ev => `
            <div class="evidence-card">
              <div class="evidence-header">
                <span class="query-ref-badge">${ev.ref || 'graph_query'}</span>
                <span style="font-size:0.72rem; color:#64748b;">Source: ${ev.source || 'graph'}</span>
              </div>
              <div class="evidence-claim">${ev.claim || ''}</div>
              ${ev.entity_ids && ev.entity_ids.length ? `
                <div class="evidence-entities">Referenced Entities: ${ev.entity_ids.join(', ')}</div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Similar Historical Cases -->
      ${simCases.length > 0 ? `
        <div class="detail-section">
          <div class="section-title">
            <span>🔗 Similar Prior Fraud Cases Retrieved from Graph Memory</span>
          </div>
          <div class="similar-cases-row">
            ${simCases.map(id => `<div class="sim-case-pill">Case #${id} (Shared Ring Cluster)</div>`).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Investigation Reasoning & Stop Reason -->
      <div class="detail-section">
        <div class="section-title">
          <span>📝 Agent Reasoning & Stop Reason</span>
        </div>
        <div class="text-box">
          ${c.summary || 'No summary recorded.'}
        </div>
        <div class="stop-reason-box">
          <strong>Investigation Stop Reason:</strong> ${data.stop_reason || 'Investigation complete.'}
        </div>
      </div>

      <!-- SAR Block -->
      <div class="detail-section">
        <div class="section-title">
          <span>🏛️ Regulatory Suspicious Activity Report (SAR)</span>
        </div>
        <div class="sar-block-container ${sar.file ? 'filed' : ''}">
          <div class="sar-title-row">
            <span class="sar-title">${sar.file ? '⚠ MANDATORY REGULATORY FILING (FinCEN / BSA-AML)' : 'SAR Not Mandated / Paused in Uncertainty Band'}</span>
            <span style="font-size:0.75rem; color:${sar.file ? '#b91c1c' : '#64748b'}; font-weight:700;">
              ${sar.file ? 'Status: FILE_REPORT Required' : 'Status: Filing Deferred'}
            </span>
          </div>
          
          <div style="font-size:0.82rem; color:#334155; margin-bottom:0.75rem;">
            <strong>Policy Reason:</strong> ${sar.reason || 'N/A'}
          </div>

          ${sar.file && sar.narrative ? `
            <div class="sar-narrative-text">${sar.narrative}</div>
            <div class="sar-meta-grid">
              <div class="sar-meta-item">
                <span>Total Exposure</span>
                <strong>$${sar.total_amount_usd ? sar.total_amount_usd.toFixed(2) : '0.00'}</strong>
              </div>
              <div class="sar-meta-item">
                <span>Activity Period</span>
                <strong>${sar.activity_dates ? sar.activity_dates.join(' to ') : 'N/A'}</strong>
              </div>
              <div class="sar-meta-item">
                <span>Identified Subjects</span>
                <strong>${sar.subjects ? sar.subjects.length : 0} Graph Entities</strong>
              </div>
            </div>
          ` : ''}
        </div>
      </div>

    </div>
  `;

  // Render the Cytoscape Graph
  initCytoscapeGraph({
    caseId: data.case_id,
    txnId: txnId,
    custId: custId,
    cardId: cardId,
    deviceProfile: deviceProfile,
    regionId: regionId,
    simCases: simCases,
    amount: exposure,
    pattern: c.pattern || "none",
    verdict: c.verdict || "uncertain",
    evidence: evidence
  });
}

function initCytoscapeGraph(data) {
  const container = document.getElementById("cy");
  if (!container || typeof cytoscape === "undefined") return;

  const elements = [];

  // 1. Center node: Transaction
  elements.push({
    data: {
      id: "txn_node",
      label: `Txn #${data.txnId}\n${data.amount}`,
      type: "Transaction",
      color: "#ea580c",
      size: 58,
      details: {
        "Vertex Type": "Transaction",
        "Transaction ID": data.txnId,
        "Amount": data.amount,
        "Case ID": data.caseId,
        "Pattern": data.pattern,
        "Verdict": data.verdict
      }
    }
  });

  // 2. Customer node
  if (data.custId && data.custId !== "N/A") {
    elements.push({
      data: {
        id: "cust_node",
        label: `Customer\n${data.custId}`,
        type: "Customer",
        color: "#4f46e5",
        size: 50,
        details: {
          "Vertex Type": "Customer",
          "Customer ID": data.custId,
          "Relation": "Owner of payment card and initiating identity"
        }
      }
    });
    elements.push({
      data: {
        id: "edge_cust",
        source: "txn_node",
        target: "cust_node",
        label: "PERFORMED_BY"
      }
    });
  }

  // 3. Card node
  if (data.cardId && data.cardId !== "N/A") {
    elements.push({
      data: {
        id: "card_node",
        label: `Card\n${data.cardId}`,
        type: "Card",
        color: "#0284c7",
        size: 50,
        details: {
          "Vertex Type": "Card",
          "Card ID": data.cardId,
          "Relation": "Payment instrument used for transaction execution"
        }
      }
    });
    elements.push({
      data: {
        id: "edge_card",
        source: "txn_node",
        target: "card_node",
        label: "USED_CARD"
      }
    });
  }

  // 4. DeviceProfile node
  if (data.deviceProfile) {
    const shortDp = data.deviceProfile.length > 28 ? data.deviceProfile.substring(0, 25) + "..." : data.deviceProfile;
    elements.push({
      data: {
        id: "dev_node",
        label: `Device\n${shortDp}`,
        type: "DeviceProfile",
        color: "#9333ea",
        size: 50,
        details: {
          "Vertex Type": "DeviceProfile",
          "Fingerprint": data.deviceProfile,
          "Relation": "Hardware and browser fingerprint associated with transaction"
        }
      }
    });
    elements.push({
      data: {
        id: "edge_dev",
        source: "txn_node",
        target: "dev_node",
        label: "USED_DEVICE"
      }
    });
  }

  // 5. BillingRegion node
  if (data.regionId) {
    elements.push({
      data: {
        id: "region_node",
        label: `${data.regionId}`,
        type: "BillingRegion",
        color: "#0d9488",
        size: 46,
        details: {
          "Vertex Type": "BillingRegion",
          "Region Identifier": data.regionId,
          "Relation": "Geographic billing address code"
        }
      }
    });
    elements.push({
      data: {
        id: "edge_region",
        source: "txn_node",
        target: "region_node",
        label: "IN_REGION"
      }
    });
  }

  // 6. Similar historical FraudCase nodes
  (data.simCases || []).slice(0, 3).forEach((simId, idx) => {
    const nodeId = `sim_${idx}`;
    elements.push({
      data: {
        id: nodeId,
        label: `Prior Case\n${simId}`,
        type: "SimilarCase",
        color: "#e11d48",
        size: 44,
        details: {
          "Vertex Type": "FraudCase (Historical)",
          "Historical Case ID": simId,
          "Graph Match": "Retrieved via get_similar_cases similarity embedding"
        }
      }
    });
    elements.push({
      data: {
        id: `edge_sim_${idx}`,
        source: "txn_node",
        target: nodeId,
        label: "SIMILAR_TO"
      }
    });
  });

  // Destroy previous Cytoscape instance if any
  if (cyInstance) {
    try {
      cyInstance.destroy();
    } catch (e) {}
  }

  // Initialize Cytoscape
  cyInstance = cytoscape({
    container: container,
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': 'data(color)',
          'label': 'data(label)',
          'color': '#0f172a',
          'font-size': '11px',
          'font-weight': '700',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-wrap': 'wrap',
          'text-max-width': '90px',
          'width': 'data(size)',
          'height': 'data(size)',
          'border-width': 2,
          'border-color': '#ffffff',
          'text-outline-color': '#ffffff',
          'text-outline-width': 2.5,
          'shadow-blur': 4,
          'shadow-color': 'rgba(0,0,0,0.15)',
          'shadow-opacity': 0.6,
          'cursor': 'pointer'
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 4,
          'border-color': '#0284c7',
          'shadow-blur': 8,
          'shadow-color': '#0284c7'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#cbd5e1',
          'target-arrow-color': '#94a3b8',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': '9px',
          'font-weight': '600',
          'color': '#475569',
          'text-background-color': '#ffffff',
          'text-background-opacity': 0.9,
          'text-background-padding': '2px',
          'text-background-shape': 'roundrectangle'
        }
      }
    ],
    layout: {
      name: 'concentric',
      concentric: function(node) {
        return node.id() === 'txn_node' ? 2 : 1;
      },
      levelWidth: function() {
        return 1;
      },
      padding: 30,
      minNodeSpacing: 35
    },
    userZoomingEnabled: true,
    userPanningEnabled: true
  });

  // Node Click Interaction
  cyInstance.on('tap', 'node', function(evt) {
    const node = evt.target;
    const details = node.data('details') || {};
    const drawer = document.getElementById("nodeDetailsDrawer");
    if (!drawer) return;

    let html = `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
      <span style="font-weight:700; color:#0f172a; font-size:0.85rem;">Selected Entity: ${node.data('type')}</span>
      <span class="badge" style="background:#f1f5f9; color:#0284c7; border:1px solid #cbd5e1;">Graph Vertex</span>
    </div><div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem;">`;

    for (const [key, val] of Object.entries(details)) {
      html += `<div style="background:#ffffff; border:1px solid #e2e8f0; padding:0.35rem 0.6rem; border-radius:4px;">
        <span style="font-size:0.68rem; color:#64748b; text-transform:uppercase; display:block;">${key}</span>
        <strong style="font-size:0.75rem; color:#0f172a; word-break:break-all;">${val}</strong>
      </div>`;
    }
    html += `</div>`;
    drawer.innerHTML = html;
  });
}

function fitGraph() {
  if (cyInstance) cyInstance.fit(30);
}

function zoomInGraph() {
  if (cyInstance) cyInstance.zoom({ level: cyInstance.zoom() * 1.25, renderedPosition: { x: cyInstance.width() / 2, y: cyInstance.height() / 2 } });
}

function zoomOutGraph() {
  if (cyInstance) cyInstance.zoom({ level: cyInstance.zoom() * 0.8, renderedPosition: { x: cyInstance.width() / 2, y: cyInstance.height() / 2 } });
}

function resetGraph() {
  if (cyInstance) {
    cyInstance.reset();
    cyInstance.fit(30);
  }
}

window.fitGraph = fitGraph;
window.zoomInGraph = zoomInGraph;
window.zoomOutGraph = zoomOutGraph;
window.resetGraph = resetGraph;
