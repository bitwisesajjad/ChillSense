// Dashboard page logic. Loads shipments + their alerts, renders the summary
// bar and the shipments table, and wires up the create-shipment form.
//
// The pure render functions are exported so tests/test_index.html can
// exercise them with fake data.

import { getShipments, getAlerts, createShipment } from './api.js';

//  pure helpers

export function statusBadgeClass(status) {
  if (status === 'active') return 'badge-active';
  if (status === 'delivered') return 'badge-delivered';
  return 'badge-other';
}

// Walk shipments + alerts and compute the four numbers we show at the top.
export function buildSummary(shipments, alertsByShipment) {
  const total = shipments.length;
  const active = shipments.filter(s => s.status === 'active').length;

  // flatten all unresolved alerts so we can count them and pick the latest
  const unresolvedAlerts = [];
  for (const s of shipments) {
    const list = alertsByShipment[s.id] || [];
    for (const a of list) {
      if (!a.is_resolved) unresolvedAlerts.push(a);
    }
  }

  // sort by created_at desc so the first one is the most recent
  // string sort works because the API returns "YYYY-MM-DD HH:MM:SS"
  unresolvedAlerts.sort((a, b) =>
    (b.created_at || '').localeCompare(a.created_at || '')
  );

  return {
    total,
    active,
    unresolved: unresolvedAlerts.length,
    latestUnresolvedMsg:
      unresolvedAlerts.length > 0 ? unresolvedAlerts[0].msg : null,
  };
}

//  DOM rendering

export function renderSummary(container, stats) {
  container.querySelector('#stat-total').textContent = String(stats.total);
  container.querySelector('#stat-active').textContent = String(stats.active);
  container.querySelector('#stat-unresolved').textContent = String(
    stats.unresolved
  );
  const msgEl = container.querySelector('#stat-msg');
  msgEl.textContent = stats.latestUnresolvedMsg ?? 'No unresolved alerts';
}

export function renderTable(tbody, shipments, alertCountsByShipment) {
  tbody.innerHTML = '';

  if (shipments.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 8;
    td.className = 'empty';
    td.textContent = 'No shipments yet';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  for (const s of shipments) {
    const tr = document.createElement('tr');
    const alertCount = alertCountsByShipment[s.id] ?? 0;
    const badgeClass = statusBadgeClass(s.status);

    // build cells one by one so we can safely set textContent (no XSS risk)
    const idTd = document.createElement('td');
    idTd.className = 'mono';
    idTd.textContent = s.id;

    const nameTd = document.createElement('td');
    const link = document.createElement('a');
    link.href = `shipment.html?id=${s.id}`;
    link.textContent = s.name;
    nameTd.appendChild(link);

    const routeTd = document.createElement('td');
    routeTd.textContent = `${s.origin} → ${s.destination}`;

    const statusTd = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = `badge ${badgeClass}`;
    badge.textContent = s.status || 'unknown';
    statusTd.appendChild(badge);

    const tempTd = document.createElement('td');
    tempTd.className = 'mono';
    tempTd.textContent = `${s.min_temperature ?? '-'} / ${s.max_temperature ?? '-'}`;

    const alertTd = document.createElement('td');
    alertTd.className = 'mono';
    if (alertCount > 0) {
      const pill = document.createElement('span');
      pill.className = 'alert-count';
      pill.textContent = alertCount;
      alertTd.appendChild(pill);
    } else {
      alertTd.textContent = '0';
    }

    const createdTd = document.createElement('td');
    createdTd.className = 'mono dim';
    createdTd.textContent = s.created_at || '';

    const actionTd = document.createElement('td');
    const viewLink = document.createElement('a');
    viewLink.href = `shipment.html?id=${s.id}`;
    viewLink.textContent = 'View';
    viewLink.className = 'action-link';
    actionTd.appendChild(viewLink);

    tr.append(
      idTd,
      nameTd,
      routeTd,
      statusTd,
      tempTd,
      alertTd,
      createdTd,
      actionTd
    );
    tbody.appendChild(tr);
  }
}

//  page bootstrap (only runs in the browser, not under tests)

async function loadDashboard() {
  const errorEl = document.getElementById('error-banner');
  const summaryEl = document.getElementById('summary-bar');
  const tbody = document.getElementById('shipments-tbody');

  errorEl.style.display = 'none';

  let shipments;
  try {
    shipments = await getShipments();
  } catch (e) {
    errorEl.textContent =
      'Failed to load shipments. Check that the API is running.';
    errorEl.style.display = 'block';
    return;
  }

  // pull alerts per shipment in parallel. if one fails we treat it as []
  // so the dashboard still renders for the others.
  const alertsByShipment = {};
  const alertCounts = {};
  await Promise.all(
    shipments.map(async s => {
      try {
        const alerts = await getAlerts(s.id);
        alertsByShipment[s.id] = alerts;
        alertCounts[s.id] = alerts.filter(a => !a.is_resolved).length;
      } catch {
        alertsByShipment[s.id] = [];
        alertCounts[s.id] = 0;
      }
    })
  );

  renderSummary(summaryEl, buildSummary(shipments, alertsByShipment));
  renderTable(tbody, shipments, alertCounts);
}

function wireForm() {
  const toggleBtn = document.getElementById('toggle-form');
  const formCard = document.getElementById('form-card');
  const form = document.getElementById('new-shipment-form');
  const formMsg = document.getElementById('form-msg');

  toggleBtn.addEventListener('click', () => {
    const isHidden = window.getComputedStyle(formCard).display === 'none';
    formCard.style.display = isHidden ? 'block' : 'none';
    toggleBtn.textContent = isHidden ? 'Cancel' : 'New Shipment';
  });

  form.addEventListener('submit', async e => {
    e.preventDefault();
    formMsg.textContent = '';
    formMsg.className = 'form-msg';

    const payload = {
      name: form.name.value.trim(),
      origin: form.origin.value.trim(),
      destination: form.destination.value.trim(),
      status: form.status.value || 'active',
      min_temperature: parseFloat(form.min_temperature.value),
      max_temperature: parseFloat(form.max_temperature.value),
    };

    try {
      await createShipment(payload);
      formMsg.textContent = 'Shipment created';
      formMsg.classList.add('ok');
      form.reset();
      // give the API cache a moment, then reload
      setTimeout(loadDashboard, 200);
    } catch (err) {
      formMsg.textContent = `Failed to create shipment: ${err.message}`;
      formMsg.classList.add('err');
    }
  });
}

if (document.getElementById('shipments-tbody')) {
  wireForm();
  loadDashboard();
}
