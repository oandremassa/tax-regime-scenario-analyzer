const $ = (id) => document.getElementById(id);
let companies = [];
let currentCompany = null;
let currentAnalysis = null;

const currency = (value) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'BRL', maximumFractionDigits: 0
}).format(Number(value || 0));

const number = (value) => Number(value || 0);

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'Request failed');
  return payload;
}

async function checkHealth() {
  try {
    const data = await api('/api/health');
    $('apiStatus').textContent = `API online · ${data.engine}`;
  } catch {
    $('apiStatus').textContent = 'API unavailable';
  }
}

async function loadCompanies() {
  companies = await api('/api/companies');
  $('companyCount').textContent = `${companies.length} companies`;
  $('companySelect').innerHTML = companies.map(c => `<option value="${c.id}">${c.legal_name}</option>`).join('');
  if (companies.length) await selectCompany(companies[0].id);
}

async function selectCompany(id) {
  const data = await api(`/api/companies/${id}`);
  currentCompany = data.company;
  currentAnalysis = data.analysis;

  $('companyMeta').innerHTML = `
    <div class="meta-block"><span>Sector</span><strong>${currentCompany.sector}</strong></div>
    <div class="meta-block"><span>Location</span><strong>${currentCompany.city || '—'} · ${currentCompany.state || '—'}</strong></div>
    <div class="meta-block"><span>Current regime</span><strong>${currentCompany.current_regime || '—'}</strong></div>`;

  if (currentAnalysis) fillAnalysis(currentAnalysis);
  $('resultsSection').classList.add('hidden');
  if (document.querySelector('.nav-item.active')?.dataset.view === 'history') loadHistory();
}

function fillAnalysis(a) {
  $('referenceYear').value = a.reference_year || 2027;
  $('annualRevenue').value = a.annual_revenue || 0;
  $('payroll').value = a.payroll || 0;
  $('operatingCosts').value = a.operating_costs || 0;
  $('serviceShare').value = a.service_share || 0;
  $('commerceShare').value = a.commerce_share || 0;
  $('sourceNote').value = a.source_note || '';
}

async function saveAndSimulate(event) {
  event.preventDefault();
  if (!currentCompany) return;
  const payload = {
    company_id: currentCompany.id,
    reference_year: Number($('referenceYear').value),
    annual_revenue: number($('annualRevenue').value),
    payroll: number($('payroll').value),
    operating_costs: number($('operatingCosts').value),
    service_share: number($('serviceShare').value),
    commerce_share: number($('commerceShare').value),
    source_note: $('sourceNote').value.trim() || 'Manual input'
  };

  currentAnalysis = await api('/api/analyses', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
  });
  const result = await api('/api/simulate', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({company_id: currentCompany.id, analysis_id: currentAnalysis.id, persist: true})
  });
  renderResults(result);
}

function renderResults(result) {
  const scenarios = result.scenarios || [];
  if (!scenarios.length) {
    $('resultsSection').classList.remove('hidden');
    $('scenarioTable').innerHTML = '<p class="muted">No scenarios available. Check the input values.</p>';
    renderAlerts(result.alerts || []);
    return;
  }

  const best = scenarios[0];
  $('bestScenario').textContent = best.name;
  $('bestTax').textContent = currency(best.estimated_tax);
  $('annualDifference').textContent = currency(result.estimated_annual_difference);

  $('scenarioTable').innerHTML = `
    <table class="table">
      <thead><tr><th>Scenario</th><th>Annual estimate</th><th>Effective rate</th><th>Monthly equivalent</th></tr></thead>
      <tbody>${scenarios.map((s, i) => `
        <tr class="${i === 0 ? 'best' : ''}"><td>${s.name}${i === 0 ? ' · lowest' : ''}</td><td>${currency(s.estimated_tax)}</td><td>${s.effective_rate.toFixed(2)}%</td><td>${currency(s.monthly_equivalent)}</td></tr>
      `).join('')}</tbody>
    </table>`;

  const max = Math.max(...scenarios.map(s => s.estimated_tax));
  $('barChart').innerHTML = scenarios.map((s, i) => `
    <div class="bar-row ${i === 0 ? 'best' : ''}">
      <div class="bar-label"><span>${s.name}</span><strong>${currency(s.estimated_tax)}</strong></div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max((s.estimated_tax / max) * 100, 4)}%"></div></div>
    </div>`).join('');

  renderAlerts(result.alerts || []);
  $('disclaimer').textContent = result.disclaimer || '';
  $('resultsSection').classList.remove('hidden');
  $('resultsSection').scrollIntoView({behavior: 'smooth', block: 'start'});
}

function renderAlerts(alerts) {
  $('alerts').innerHTML = alerts.length
    ? alerts.map(a => `<div class="alert">${a}</div>`).join('')
    : '<div class="alert ok">No input validation warnings.</div>';
}

async function importCsv(event) {
  event.preventDefault();
  const file = $('csvFile').files[0];
  if (!file || !currentCompany) return;
  const fd = new FormData();
  fd.append('company_id', currentCompany.id);
  fd.append('file', file);
  const feedback = $('importFeedback');
  feedback.className = 'feedback';
  feedback.textContent = 'Importing...';
  try {
    const result = await api('/api/import-monthly', {method: 'POST', body: fd});
    $('annualRevenue').value = result.annual_revenue;
    $('payroll').value = result.payroll;
    $('operatingCosts').value = result.operating_costs;
    feedback.classList.add('success');
    feedback.textContent = `${result.rows_loaded} rows loaded. Annual fields were updated.`;
  } catch (err) {
    feedback.classList.add('error');
    feedback.textContent = err.message;
  }
}

async function loadHistory() {
  if (!currentCompany) return;
  const data = await api(`/api/history/${currentCompany.id}`);
  const items = data.simulations || [];
  $('historyList').innerHTML = items.length ? items.map(item => `
    <div class="history-item">
      <time>${new Date(item.created_at).toLocaleString()}</time>
      <div><strong>${item.result.recommended_scenario || 'No result'}</strong><br><span>Analysis #${item.analysis_id} · ${item.engine_version}</span></div>
      <strong>${currency(item.result.scenarios?.[0]?.estimated_tax || 0)}</strong>
    </div>`).join('') : '<p class="muted">No simulations saved for this company yet.</p>';
}

function switchView(view) {
  document.querySelectorAll('.nav-item').forEach(btn => btn.classList.toggle('active', btn.dataset.view === view));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  $(`${view}View`).classList.add('active');
  if (view === 'history') loadHistory();
}

document.querySelectorAll('.nav-item').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.view)));
$('companySelect').addEventListener('change', e => selectCompany(Number(e.target.value)));
$('analysisForm').addEventListener('submit', saveAndSimulate);
$('importForm').addEventListener('submit', importCsv);

checkHealth();
loadCompanies();
