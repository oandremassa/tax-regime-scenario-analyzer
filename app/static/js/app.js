const state = {
  bootstrap: null,
  company: null,
  analyses: [],
  analysisId: null,
  detail: null,
  simulation: null,
  dashboard: null,
  history: null,
  rules: null,
  validationFilter: "all",
  view: "dashboard",
};

const $ = (id) => document.getElementById(id);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const viewMeta = {
  dashboard: ["Overview", "Executive Dashboard"],
  companies: ["Master data", "Companies"],
  workspace: ["Analysis inputs", "Financial Workspace"],
  sources: ["Evidence layer", "Data Sources"],
  validations: ["Control layer", "Validation Center"],
  analysis: ["Comparative engine", "Tax Analysis"],
  report: ["Client-ready output", "Executive Report"],
  history: ["Traceability", "History & Audit"],
  rules: ["Governance", "Rules & Sources"],
};

async function api(url, options = {}) {
  const response = await fetch(url, options);
  let data;
  try { data = await response.json(); } catch { data = {}; }
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function money(value, compact = false) {
  const n = Number(value || 0);
  if (compact && Math.abs(n) >= 1_000_000) return `R$ ${(n / 1_000_000).toFixed(2)}M`;
  if (compact && Math.abs(n) >= 1_000) return `R$ ${(n / 1_000).toFixed(1)}k`;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "BRL", maximumFractionDigits: 2 }).format(n);
}
function pct(value, digits = 2) { return `${Number(value || 0).toFixed(digits)}%`; }
function esc(value) { return String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c])); }
function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-GB", { day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" }).format(d);
}
function shortMonth(value) {
  if (!value || value.length < 7) return value || "—";
  const [y,m] = value.split("-");
  return new Intl.DateTimeFormat("en", { month:"short" }).format(new Date(Number(y), Number(m)-1, 1));
}
function initials(name) { return String(name || "?").split(/\s+/).slice(0,2).map(x => x[0] || "").join("").toUpperCase(); }

function toast(message) {
  const el = $("toast"); el.textContent = message; el.classList.add("show");
  clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove("show"), 2300);
}

function aggregate(rows = []) {
  const result = {commerce_revenue:0,industry_revenue:0,service_revenue:0,payroll:0,costs:0,expenses:0,current_tax_paid:0,revenue:0,operating_profit:0,margin:0};
  rows.forEach(r => {
    ["commerce_revenue","industry_revenue","service_revenue","payroll","costs","expenses","current_tax_paid"].forEach(k => result[k] += Number(r[k] || 0));
  });
  result.revenue = result.commerce_revenue + result.industry_revenue + result.service_revenue;
  result.operating_profit = result.revenue - result.payroll - result.costs - result.expenses;
  result.margin = result.revenue ? result.operating_profit / result.revenue * 100 : 0;
  result.factor_r = result.revenue ? result.payroll / result.revenue * 100 : 0;
  return result;
}

async function loadBootstrap(companyId = null) {
  const q = companyId ? `?company_id=${companyId}` : "";
  state.bootstrap = await api(`/api/bootstrap${q}`);
  state.company = state.bootstrap.selected_company;
  state.analyses = state.bootstrap.analyses || [];
  state.analysisId = state.bootstrap.selected_analysis_id;
  $("engineVersion").textContent = state.bootstrap.engine_version || "—";
  renderContextSelectors();
}

async function loadCompanyContext(companyId) {
  const data = await api(`/api/companies/${companyId}`);
  state.company = data.company;
  state.analyses = data.analyses || [];
  state.analysisId = state.analyses[0]?.id || null;
  renderContextSelectors();
  await loadAnalysisContext();
}

async function loadAnalysisContext() {
  if (!state.analysisId) {
    state.detail = null; state.simulation = null; state.history = null;
    renderAll(); return;
  }
  state.detail = await api(`/api/analyses/${state.analysisId}`);
  state.company = state.detail.company;
  state.simulation = state.detail.latest_simulation?.result || null;
  state.history = await api(`/api/history/${state.company.id}`);
  renderContextSelectors();
  renderAll();
}

async function loadGlobal() {
  state.dashboard = await api("/api/dashboard");
  state.rules = await api("/api/rules/status");
}

function renderContextSelectors() {
  const companySelect = $("companySelect");
  const analysisSelect = $("analysisSelect");
  const companies = state.bootstrap?.companies || [];
  companySelect.innerHTML = companies.map(c => `<option value="${c.id}">${esc(c.trade_name || c.legal_name)}</option>`).join("");
  if (state.company) companySelect.value = String(state.company.id);
  analysisSelect.innerHTML = state.analyses.length ? state.analyses.map(a => `<option value="${a.id}">${esc(a.title)}</option>`).join("") : `<option value="">No analysis</option>`;
  if (state.analysisId) analysisSelect.value = String(state.analysisId);
}

function gotoView(view) {
  state.view = view;
  $$(".nav-item").forEach(x => x.classList.toggle("active", x.dataset.view === view));
  $$(".view").forEach(x => x.classList.toggle("active", x.dataset.viewPanel === view));
  const meta = viewMeta[view] || ["Workspace", view];
  $("pageKicker").textContent = meta[0]; $("pageTitle").textContent = meta[1];
  $("sidebar").classList.remove("open");
  if (view === "report") renderReport();
  window.scrollTo({top:0, behavior:"smooth"});
}

function renderAll() {
  renderDashboard(); renderCompanies(); renderWorkspace(); renderSources(); renderValidations(); renderAnalysis(); renderReport(); renderHistory(); renderRules();
}

function renderDashboard() {
  const detail = state.detail;
  if (!detail) return;
  const rows = detail.monthly || [];
  const agg = aggregate(rows);
  const sim = state.simulation;
  $("dashboardCompany").textContent = `${state.company.trade_name || state.company.legal_name} · ${detail.analysis.title}`;
  $("dashboardContext").textContent = `${state.company.city || "—"}, ${state.company.state || "—"} · ${state.company.current_regime || "Regime not informed"} · ${detail.analysis.period_start} to ${detail.analysis.period_end}`;
  $("periodChip").textContent = `FY${detail.analysis.fiscal_year}`;
  $("kpiRevenue").textContent = money(agg.revenue, true);
  $("kpiCurrentTax").textContent = money(agg.current_tax_paid, true);
  $("kpiCurrentTaxRate").textContent = agg.revenue ? `${pct(agg.current_tax_paid / agg.revenue * 100)} effective` : "No baseline";
  const pending = detail.validations.filter(v => v.status === "pending");
  const blocking = pending.filter(v => v.severity === "blocking");
  $("kpiValidations").textContent = String(pending.length);
  $("kpiBlocking").textContent = `${blocking.length} blocking`;
  $("kpiDocuments").textContent = String(detail.documents.length);
  $("navValidationCount").textContent = String(pending.length);

  const maxRevenue = Math.max(...rows.map(r => Number(r.commerce_revenue)+Number(r.industry_revenue)+Number(r.service_revenue)), 1);
  $("revenueChart").innerHTML = rows.map(r => {
    const c=Number(r.commerce_revenue||0), i=Number(r.industry_revenue||0), s=Number(r.service_revenue||0), total=c+i+s;
    const h=Math.max(total/maxRevenue*100,2);
    const sum=total||1;
    return `<div class="month-bar-wrap" title="${esc(r.month)} · ${money(total)}"><div class="month-bar-stack" style="--h:${h}"><span class="bar-segment industry" style="height:${i/sum*100}%"></span><span class="bar-segment commerce" style="height:${c/sum*100}%"></span><span class="bar-segment service" style="height:${s/sum*100}%"></span></div><span class="month-label">${shortMonth(r.month)}</span></div>`;
  }).join("");

  const total = agg.revenue || 1;
  const sPct = agg.service_revenue/total*100, cPct=agg.commerce_revenue/total*100, iPct=agg.industry_revenue/total*100;
  $("mixDonut").style.background = `conic-gradient(#2b7b63 0 ${sPct}%, #506e91 ${sPct}% ${sPct+cPct}%, #c4a25c ${sPct+cPct}% 100%)`;
  $("donutTotal").textContent = money(agg.revenue, true);
  const mix = [
    ["Services",sPct,"#2b7b63",agg.service_revenue], ["Commerce",cPct,"#506e91",agg.commerce_revenue], ["Industry",iPct,"#c4a25c",agg.industry_revenue]
  ];
  $("mixList").innerHTML = mix.map(([name,p,color,val]) => `<div class="mix-row"><span class="mix-dot" style="background:${color}"></span><span>${name}</span><strong>${p.toFixed(1)}%</strong></div>`).join("");

  renderDashboardScenarios(sim);
  const docsReady = detail.documents.length ? 100 : 25;
  const coverage = Math.min((rows.length/12)*100,100);
  const validationReady = pending.length ? Math.max(20, 100-pending.length*12) : 100;
  $("readinessPanel").innerHTML = [
    ["Period coverage",coverage,`${rows.length}/12 months`], ["Evidence layer",docsReady,`${detail.documents.length} source(s)`], ["Validation readiness",validationReady,`${pending.length} pending`]
  ].map(([label,value,meta])=>`<div class="readiness-item"><div class="readiness-top"><span>${label}</span><strong>${meta}</strong></div><div class="progress"><span style="width:${value}%"></span></div></div>`).join("") + `<div class="readiness-note">${blocking.length ? `${blocking.length} blocking validation(s) still require review before this case should be treated as decision-ready.` : "No blocking validations are currently pending. Human review still applies to the illustrative calculation model."}</div>`;

  const activity = state.history?.audit?.slice(0,5) || [];
  $("dashboardActivity").innerHTML = activity.length ? activity.map(a=>`<div class="activity-item"><span class="activity-dot"></span><div><strong>${esc(a.action)} · ${esc(a.entity)}</strong><span>${esc(a.field_name || a.new_value || "Workflow event")}</span></div><span class="activity-time">${formatDate(a.created_at).split(",")[0]}</span></div>`).join("") : `<div class="empty">No activity yet.</div>`;

  if (sim?.best_scenario) {
    const best = sim.best_scenario;
    $("executiveSignal").innerHTML = `<div class="signal-hero"><span>Lowest mathematical estimate</span><strong>${esc(best.label)}</strong><small>${pct(best.effective_rate)} effective · ${sim.status === "review_ready" ? "review-ready dataset" : "preliminary dataset"}</small></div><div class="signal-grid"><div class="signal-metric"><span>Annual estimate</span><strong>${money(best.total_tax,true)}</strong></div><div class="signal-metric"><span>Delta vs highest</span><strong>${money(sim.potential_savings_vs_highest,true)}</strong></div></div>`;
  } else {
    $("executiveSignal").innerHTML = `<div class="empty">Run the scenario engine to produce the executive signal.</div>`;
  }
}

function renderDashboardScenarios(sim) {
  const target=$("dashboardScenarioBars");
  if (!sim?.scenarios?.length) { target.innerHTML=`<div class="empty">No simulation available. Run the scenario engine.</div>`; return; }
  const max=Math.max(...sim.scenarios.map(s=>s.total_tax),1);
  target.innerHTML=sim.scenarios.map(s=>`<div class="scenario-bar-row ${s.key===sim.best_scenario?.key?"best":""}"><div class="scenario-bar-label"><strong>${esc(s.label)}</strong><span>${esc(s.subtitle)}</span></div><div class="scenario-track"><span style="width:${Math.max(s.total_tax/max*100,3)}%"></span></div><div class="scenario-bar-value">${money(s.total_tax,true)}</div><div class="scenario-rate">${pct(s.effective_rate)}</div></div>`).join("");
}

function renderCompanies() {
  const companies = state.bootstrap?.companies || [];
  const q = ($("companySearch")?.value || "").toLowerCase();
  if ($("companyList")) $("companyList").innerHTML = companies.filter(c => `${c.legal_name} ${c.trade_name} ${c.identifier}`.toLowerCase().includes(q)).map(c=>`<div class="company-item ${c.id===state.company?.id?"active":""}" data-company-id="${c.id}"><div class="company-avatar">${initials(c.trade_name||c.legal_name)}</div><div><strong>${esc(c.trade_name||c.legal_name)}</strong><span>${esc(c.identifier)} · ${esc(c.current_regime||"No regime")}</span></div></div>`).join("");
  if (!state.company) return;
  $("companyProfileTitle").textContent = state.company.trade_name || state.company.legal_name;
  const f = $("companyForm");
  if (!f) return;
  ["legal_name","trade_name","identifier","cnae","city","state","current_regime","service_annex","notes"].forEach(k => { if (f.elements[k]) f.elements[k].value = state.company[k] ?? ""; });
  f.elements.iss_rate.value = (Number(state.company.iss_rate||0)*100).toFixed(2);
  f.elements.icms_rate.value = (Number(state.company.icms_rate||0)*100).toFixed(2);
}

function ensureMonthlyRows() {
  const existing = new Map((state.detail?.monthly||[]).map(r=>[r.month,{...r}]));
  const year = state.detail?.analysis?.fiscal_year || new Date().getFullYear();
  const rows=[];
  for(let m=1;m<=12;m++){
    const month=`${year}-${String(m).padStart(2,"0")}`;
    rows.push(existing.get(month)||{month,commerce_revenue:0,industry_revenue:0,service_revenue:0,payroll:0,costs:0,expenses:0,current_tax_paid:0});
  }
  return rows;
}

function renderWorkspace() {
  if (!state.detail) return;
  const rows = ensureMonthlyRows(); const agg=aggregate(rows);
  const tiles=[["Annual revenue",money(agg.revenue,true)],["Payroll",money(agg.payroll,true)],["Costs + expenses",money(agg.costs+agg.expenses,true)],["Operating margin",pct(agg.margin)],["Factor R proxy",pct(agg.factor_r)]];
  $("workspaceSummary").innerHTML=tiles.map(([a,b])=>`<div class="summary-tile"><span>${a}</span><strong>${b}</strong></div>`).join("");
  $("monthlyTableBody").innerHTML=rows.map(r=>{
    const total=Number(r.commerce_revenue)+Number(r.industry_revenue)+Number(r.service_revenue);
    return `<tr data-month="${r.month}"><td>${shortMonth(r.month)} ${r.month.slice(0,4)}</td>${["commerce_revenue","industry_revenue","service_revenue","payroll","costs","expenses","current_tax_paid"].map(k=>`<td><input data-field="${k}" type="number" min="0" step="0.01" value="${Number(r[k]||0).toFixed(2)}"></td>`).join("")}<td class="row-total">${money(total,true)}</td></tr>`;
  }).join("");
  $("monthlyTableFoot").innerHTML=`<tr><td>YEAR TOTAL</td><td>${money(agg.commerce_revenue,true)}</td><td>${money(agg.industry_revenue,true)}</td><td>${money(agg.service_revenue,true)}</td><td>${money(agg.payroll,true)}</td><td>${money(agg.costs,true)}</td><td>${money(agg.expenses,true)}</td><td>${money(agg.current_tax_paid,true)}</td><td>${money(agg.revenue,true)}</td></tr>`;
  const existingMonths=new Set((state.detail.monthly||[]).map(r=>r.month));
  $("coveragePanel").innerHTML=`<div class="metric-stack"><div class="metric-line"><span>Loaded months</span><strong>${existingMonths.size}/12</strong></div><div class="metric-line"><span>Analysis period</span><strong>${state.detail.analysis.period_start} → ${state.detail.analysis.period_end}</strong></div><div class="metric-line"><span>Source note</span><strong>${esc(state.detail.analysis.source_note||"Manual / synthetic demo")}</strong></div></div><div class="coverage-grid">${rows.map(r=>`<div class="coverage-month ${existingMonths.has(r.month)?"":"missing"}">${shortMonth(r.month).slice(0,1)}</div>`).join("")}</div>`;
  $("profitPanel").innerHTML=`<div class="metric-stack"><div class="metric-line"><span>Revenue</span><strong>${money(agg.revenue)}</strong></div><div class="metric-line"><span>Payroll</span><strong>${money(agg.payroll)}</strong></div><div class="metric-line"><span>Costs</span><strong>${money(agg.costs)}</strong></div><div class="metric-line"><span>Expenses</span><strong>${money(agg.expenses)}</strong></div><div class="metric-line"><span>Operating profit proxy</span><strong class="${agg.operating_profit>=0?"good-text":"danger-text"}">${money(agg.operating_profit)}</strong></div><div class="metric-line"><span>Operating margin</span><strong>${pct(agg.margin)}</strong></div></div>`;
}

function renderSources(){
  const docs=state.detail?.documents||[];
  $("documentCountChip").textContent=`${docs.length} document${docs.length===1?"":"s"}`;
  $("documentsTable").innerHTML=docs.length?docs.map(d=>`<tr><td><strong>${esc(d.original_name)}</strong></td><td>${esc((d.doc_type||"—").toUpperCase())}</td><td>${esc(d.parser_name||"—")}</td><td><span class="status-pill ${d.status==="processed"?"good":"warn"}">${esc(d.status)}</span></td><td>${formatDate(d.uploaded_at)}</td></tr>`).join(""):`<tr><td colspan="5"><div class="empty">No evidence documents uploaded for this analysis.</div></td></tr>`;
}

function filteredValidations(){
  const items=state.detail?.validations||[];
  if(state.validationFilter==="all") return items;
  if(state.validationFilter==="blocking") return items.filter(v=>v.severity==="blocking"&&v.status==="pending");
  return items.filter(v=>v.status===state.validationFilter);
}
function renderValidations(){
  const items=state.detail?.validations||[];
  const pending=items.filter(v=>v.status==="pending");
  const blocking=pending.filter(v=>v.severity==="blocking");
  const validated=items.filter(v=>v.status==="validated");
  const resolved=items.filter(v=>v.status==="resolved");
  $("validationStats").innerHTML=[["Open",pending.length],["Blocking",blocking.length],["Validated",validated.length],["Auto-resolved",resolved.length]].map(([a,b])=>`<div class="validation-stat"><span>${a}</span><strong>${b}</strong></div>`).join("");
  $("navValidationCount").textContent=String(pending.length);
  const shown=filteredValidations();
  $("validationList").innerHTML=shown.length?shown.map(v=>`<article class="validation-card ${esc(v.severity)} ${v.status==="validated"?"validated":""}"><span class="severity-bar"></span><div><h4>${esc(v.title)}</h4><p>${esc(v.detail||"")}</p><div class="validation-meta"><span>${esc(v.code)}</span><span>${esc(v.severity)}</span><span>${esc(v.status)}</span></div></div><div class="validation-actions">${v.status!=="validated"?`<button class="mini-btn good validation-action" data-id="${v.id}" data-status="validated">Mark validated</button>`:`<button class="mini-btn validation-action" data-id="${v.id}" data-status="pending">Reopen</button>`}</div></article>`).join(""):`<div class="empty">No validation items in this filter.</div>`;
}

function renderAnalysis(){
  const sim=state.simulation;
  if(!sim?.scenarios?.length){
    $("analysisStatus").innerHTML=`<div class="status-banner"><div><strong>No current simulation</strong><br><span>Run the engine to compare the three tax regimes.</span></div></div>`;
    $("scenarioCards").innerHTML=`<div class="empty" style="grid-column:1/-1">No scenario results yet.</div>`;
    $("componentScenarioSelect").innerHTML=""; $("componentsTable").innerHTML=""; $("assumptionsPanel").innerHTML=""; $("analysisOperatingProfile").innerHTML=""; $("scenarioDelta").innerHTML=""; return;
  }
  $("analysisStatus").innerHTML=`<div class="status-banner ${sim.status}"><div><strong>${sim.status==="review_ready"?"Dataset ready for human review":"Preliminary result — validation attention required"}</strong><br><span>${sim.blocking_validations} generated blocking check(s) · engine ${esc(sim.engine_version)}</span></div><span>${esc(sim.portfolio_disclaimer)}</span></div>`;
  const highest=Math.max(...sim.scenarios.map(s=>s.total_tax),1);
  $("scenarioCards").innerHTML=sim.scenarios.map(s=>`<article class="scenario-card ${s.key===sim.best_scenario?.key?"best":""}">${s.key===sim.best_scenario?.key?`<span class="best-ribbon">Lowest estimate</span>`:""}<h3>${esc(s.label)}</h3><span class="subtitle">${esc(s.subtitle)}</span><div class="scenario-number">${money(s.total_tax,true)}</div><div class="scenario-effective">${pct(s.effective_rate)} effective rate</div><hr><div class="scenario-meta"><span>Monthly average</span><strong>${money(s.monthly_estimate,true)}</strong></div><div class="scenario-meta"><span>Delta vs lowest</span><strong>${money(s.difference_vs_lowest,true)}</strong></div><div class="scenario-meta"><span>Burden index</span><strong>${(s.total_tax/highest*100).toFixed(0)}</strong></div></article>`).join("");
  const select=$("componentScenarioSelect"); const prev=select.value;
  select.innerHTML=sim.scenarios.map(s=>`<option value="${s.key}">${esc(s.label)}</option>`).join("");
  select.value=sim.scenarios.some(s=>s.key===prev)?prev:sim.best_scenario.key;
  renderComponents();
  const a=sim.aggregates;
  const values=[["Payroll / revenue",a.revenue?a.payroll/a.revenue*100:0],["Costs / revenue",a.revenue?a.costs/a.revenue*100:0],["Expenses / revenue",a.revenue?a.expenses/a.revenue*100:0],["Operating margin",a.margin],["Factor R proxy",a.factor_r*100]];
  $("analysisOperatingProfile").innerHTML=`<div class="profile-bars">${values.map(([label,val])=>`<div class="profile-row"><span>${label}</span><div class="profile-track"><span style="width:${Math.max(Math.min(val,100),0)}%"></span></div><strong>${pct(val)}</strong></div>`).join("")}</div>`;
  const sorted=[...sim.scenarios].sort((a,b)=>a.total_tax-b.total_tax); const best=sorted[0];
  $("scenarioDelta").innerHTML=sorted.slice(1).map(s=>`<div class="delta-card"><span>${esc(s.label)} vs ${esc(best.label)}</span><strong>+ ${money(s.total_tax-best.total_tax,true)}</strong></div>`).join("")+`<div class="delta-card"><span>Potential spread: highest vs lowest</span><strong>${money(sim.potential_savings_vs_highest,true)}</strong></div><div class="delta-card"><span>Current tax baseline in source data</span><strong>${money(sim.current_tax_baseline,true)}</strong></div>`;
}
function renderComponents(){
  const sim=state.simulation;if(!sim?.scenarios?.length)return;
  const key=$("componentScenarioSelect").value||sim.best_scenario.key; const s=sim.scenarios.find(x=>x.key===key)||sim.scenarios[0];
  const entries=Object.entries(s.components||{}); const total=s.total_tax||1; const revenue=sim.aggregates.revenue||1;
  $("componentsTable").innerHTML=entries.map(([name,val])=>`<tr><td><strong>${esc(name)}</strong></td><td>${money(val)}</td><td>${pct(val/total*100)}</td><td>${pct(val/revenue*100)}</td></tr>`).join("");
  $("assumptionsPanel").innerHTML=(s.assumptions||[]).map((x,i)=>`<div class="assumption"><span class="assumption-index">${i+1}</span><span>${esc(x)}</span></div>`).join("");
}

function renderReport(){
  const sim=state.simulation; const detail=state.detail;
  if(!detail) return;
  $("reportCompanyName").textContent=state.company.legal_name;
  $("reportPeriod").textContent=`${detail.analysis.title} · ${detail.analysis.period_start} → ${detail.analysis.period_end}`;
  $("reportTimestamp").textContent=`Generated ${new Date().toLocaleString("en-GB")}`;
  if(!sim?.best_scenario){
    $("reportKpis").innerHTML=`<div class="report-kpi"><span>Status</span><strong>No simulation</strong></div>`;
    $("reportConclusion").innerHTML="Run the scenario engine to populate this report."; $("reportScenarios").innerHTML=""; $("reportTaxDetail").innerHTML=""; $("reportValidations").innerHTML=""; return;
  }
  const a=sim.aggregates,b=sim.best_scenario;
  $("reportKpis").innerHTML=[["Annual revenue",money(a.revenue,true)],["Lowest estimate",money(b.total_tax,true)],["Effective rate",pct(b.effective_rate)],["Scenario spread",money(sim.potential_savings_vs_highest,true)]].map(([x,y])=>`<div class="report-kpi"><span>${x}</span><strong>${y}</strong></div>`).join("");
  const quality = sim.status==="review_ready" ? "The dataset has no generated blocking checks, but professional validation remains required." : `The result is preliminary because ${sim.blocking_validations} blocking check(s) were generated.`;
  $("reportConclusion").innerHTML=`For the synthetic FY${detail.analysis.fiscal_year} dataset, <strong>${esc(b.label)}</strong> produces the lowest mathematical estimate at <strong>${money(b.total_tax)}</strong>, equivalent to <strong>${pct(b.effective_rate)}</strong> of annual revenue. The spread between the highest and lowest modeled scenarios is <strong>${money(sim.potential_savings_vs_highest)}</strong>. ${quality} The highlighted scenario is a comparison output, not a legal eligibility recommendation.`;
  $("reportScenarios").innerHTML=sim.scenarios.map(s=>`<div class="report-scenario ${s.key===b.key?"best":""}"><span>${esc(s.label)}</span><strong>${money(s.total_tax,true)}</strong><small>${pct(s.effective_rate)} effective · ${esc(s.subtitle)}</small></div>`).join("");
  $("reportTaxDetail").innerHTML=`<div class="report-component-grid">${sim.scenarios.map(s=>`<div class="report-component-col"><h4>${esc(s.label)}</h4>${Object.entries(s.components).map(([k,v])=>`<div class="report-component-row"><span>${esc(k)}</span><strong>${money(v,true)}</strong></div>`).join("")}</div>`).join("")}</div>`;
  const validations=state.detail.validations||[];
  $("reportValidations").innerHTML=validations.length?validations.map(v=>`<div class="report-validation"><b>${esc(v.severity.toUpperCase())}</b><span>${esc(v.title)} — ${esc(v.status)}</span></div>`).join(""):`<div class="report-validation"><b>INFO</b><span>No generated validation items.</span></div>`;
}

function renderHistory(){
  const h=state.history||{simulations:[],documents:[],audit:[]};
  $("historySimulations").innerHTML=h.simulations.length?h.simulations.map(s=>{const b=s.result.best_scenario;return `<tr><td>#${s.id}</td><td>${esc(s.title)}</td><td>${esc(b?.label||"—")}</td><td>${b?pct(b.effective_rate):"—"}</td><td>${esc(s.engine_version)}</td><td>${formatDate(s.created_at)}</td></tr>`}).join(""):`<tr><td colspan="6"><div class="empty">No simulations.</div></td></tr>`;
  $("historyDocuments").innerHTML=h.documents.length?h.documents.map(d=>`<tr><td>#${d.id}</td><td>${esc(d.original_name)}</td><td>${esc(d.doc_type||"—")}</td><td>${esc(d.parser_name||"—")}</td><td>${esc(d.status)}</td><td>${formatDate(d.uploaded_at)}</td></tr>`).join(""):`<tr><td colspan="6"><div class="empty">No documents.</div></td></tr>`;
  $("historyAudit").innerHTML=h.audit.length?h.audit.map(a=>`<tr><td>${formatDate(a.created_at)}</td><td>${esc(a.action)}</td><td>${esc(a.entity)}${a.entity_id?` #${a.entity_id}`:""}</td><td>${esc(a.field_name||"—")}</td><td>${esc(a.old_value||"—")}</td><td>${esc(a.new_value||"—")}</td></tr>`).join(""):`<tr><td colspan="6"><div class="empty">No audit records.</div></td></tr>`;
}

function renderRules(){
  const r=state.rules;if(!r)return;
  $("rulesSources").innerHTML=(r.sources||[]).map(s=>`<tr><td><strong>${esc(s.title)}</strong></td><td>${esc(s.topic||"—")}</td><td><span class="status-pill ${s.status==="reviewed"?"good":"warn"}">${esc(s.status)}</span></td><td>${esc(s.version||"—")}</td></tr>`).join("");
  $("engineGovernance").innerHTML=`<div class="governance-list"><div class="governance-item"><span>Engine version</span><strong>${esc(r.engine_version)}</strong></div><div class="governance-item"><span>Calculation mode</span><strong>Portfolio demo</strong></div><div class="governance-item"><span>Human review</span><strong class="warn-text">Required</strong></div><div class="governance-item"><span>Production tax advice</span><strong class="danger-text">No</strong></div><div class="governance-item"><span>Reference sources</span><strong>${r.sources.length}</strong></div><div class="governance-item"><span>Configured rules</span><strong>${r.rules.length}</strong></div></div>`;
  $("rulesTable").innerHTML=(r.rules||[]).map(x=>`<tr><td>${esc(x.regime)}</td><td><strong>${esc(x.rule_name)}</strong></td><td>${Number(x.rule_value).toFixed(4)}</td><td>${esc(x.unit||"—")}</td><td><span class="status-pill warn">${esc(x.status)}</span></td><td>${esc(x.effective_from||"—")}</td></tr>`).join("");
}

function readMonthlyTable(){
  return $$("#monthlyTableBody tr").map(tr=>{const row={month:tr.dataset.month};tr.querySelectorAll("input[data-field]").forEach(i=>row[i.dataset.field]=Number(i.value||0));return row;});
}

async function saveMonthly(){
  if(!state.analysisId)return;
  const rows=readMonthlyTable();
  await api(`/api/analyses/${state.analysisId}/monthly`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({rows})});
  toast("Financial workspace saved"); await loadAnalysisContext();
}
async function runAnalysis(){
  if(!state.analysisId)return;
  $("runAnalysisBtn").disabled=true; $("runAnalysisBtn").textContent="Running…";
  try{
    state.simulation=await api("/api/simulate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({analysis_id:state.analysisId})});
    state.detail=await api(`/api/analyses/${state.analysisId}`); state.history=await api(`/api/history/${state.company.id}`); state.dashboard=await api("/api/dashboard");
    renderAll(); toast("Scenario analysis completed");
  }catch(e){toast(e.message)}finally{$("runAnalysisBtn").disabled=false;$("runAnalysisBtn").textContent="Run scenario engine";}
}

async function uploadFiles(files){
  if(!files?.length||!state.analysisId)return;
  const fd=new FormData(); fd.append("company_id",state.company.id);fd.append("analysis_id",state.analysisId);[...files].forEach(f=>fd.append("files",f));
  $("uploadStatus").innerHTML=`<div class="upload-result">Processing ${files.length} file(s)…</div>`;
  try{const res=await api("/api/upload",{method:"POST",body:fd});$("uploadStatus").innerHTML=res.files.map(f=>`<div class="upload-result"><strong>${esc(f.name)}</strong> · ${esc(f.parser||"stored")} · ${f.monthly_rows_imported||0} monthly row(s) imported${f.warnings?.length?` · ${esc(f.warnings.join(" "))}`:""}</div>`).join("");toast("Document intake completed");await loadAnalysisContext();}catch(e){$("uploadStatus").innerHTML=`<div class="upload-result danger-text">${esc(e.message)}</div>`;}
}

async function updateValidation(id,status){
  await api(`/api/validations/${id}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({status})});
  state.detail=await api(`/api/analyses/${state.analysisId}`); state.history=await api(`/api/history/${state.company.id}`);renderAll();toast(status==="validated"?"Validation marked as reviewed":"Validation reopened");
}

function openModal(id){$(id).classList.add("open")}
function closeModals(){$$(".modal-backdrop").forEach(x=>x.classList.remove("open"))}

function wireEvents(){
  $$(".nav-item").forEach(b=>b.addEventListener("click",()=>gotoView(b.dataset.view)));
  $$('[data-goto]').forEach(b=>b.addEventListener("click",()=>gotoView(b.dataset.goto)));
  $("mobileMenu").addEventListener("click",()=>$("sidebar").classList.toggle("open"));
  $("refreshBtn").addEventListener("click",async()=>{await loadGlobal();await loadAnalysisContext();toast("Workspace refreshed")});
  $("companySelect").addEventListener("change",async e=>{await loadCompanyContext(Number(e.target.value));});
  $("analysisSelect").addEventListener("change",async e=>{state.analysisId=Number(e.target.value)||null;await loadAnalysisContext();});
  $("dashboardRunBtn").addEventListener("click",async()=>{await runAnalysis();gotoView("analysis")});
  $("runAnalysisBtn").addEventListener("click",runAnalysis);
  $("saveMonthlyBtn").addEventListener("click",saveMonthly);
  $("componentScenarioSelect").addEventListener("change",renderComponents);
  $("printReportBtn").addEventListener("click",()=>window.print());
  $("companySearch").addEventListener("input",renderCompanies);
  $("companyList").addEventListener("click",async e=>{const item=e.target.closest("[data-company-id]");if(item)await loadCompanyContext(Number(item.dataset.companyId));});
  $("companyForm").addEventListener("submit",async e=>{e.preventDefault();const f=e.currentTarget;const body=Object.fromEntries(new FormData(f).entries());body.iss_rate=Number(body.iss_rate||0)/100;body.icms_rate=Number(body.icms_rate||0)/100;delete body.identifier;const updated=await api(`/api/companies/${state.company.id}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});state.company=updated;state.bootstrap.companies=state.bootstrap.companies.map(c=>c.id===updated.id?updated:c);$("companySaveStatus").textContent="Saved";renderAll();renderContextSelectors();toast("Company profile saved");setTimeout(()=>$("companySaveStatus").textContent="",1600)});
  $("newCompanyBtn").addEventListener("click",()=>openModal("companyModal")); $("newAnalysisBtn").addEventListener("click",()=>openModal("analysisModal"));
  $$(".modal-close").forEach(x=>x.addEventListener("click",closeModals)); $$(".modal-backdrop").forEach(x=>x.addEventListener("click",e=>{if(e.target===e.currentTarget)closeModals()}));
  $("newCompanyForm").addEventListener("submit",async e=>{e.preventDefault();const body=Object.fromEntries(new FormData(e.currentTarget).entries());const c=await api("/api/companies",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});closeModals();await loadBootstrap(c.id);await loadCompanyContext(c.id);toast("Company created");});
  $("newAnalysisForm").addEventListener("submit",async e=>{e.preventDefault();const body=Object.fromEntries(new FormData(e.currentTarget).entries());body.company_id=state.company.id;body.fiscal_year=Number(body.fiscal_year);body.period_start=`${body.fiscal_year}-01`;body.period_end=body.period_end||`${body.fiscal_year}-12`;const a=await api("/api/analyses",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});closeModals();state.analyses.unshift(a);state.analysisId=a.id;renderContextSelectors();await loadAnalysisContext();toast("Analysis created");});
  const dz=$("dropZone"),fi=$("fileInput");dz.addEventListener("click",()=>fi.click());fi.addEventListener("change",()=>uploadFiles(fi.files));["dragenter","dragover"].forEach(n=>dz.addEventListener(n,e=>{e.preventDefault();dz.classList.add("dragover")}));["dragleave","drop"].forEach(n=>dz.addEventListener(n,e=>{e.preventDefault();dz.classList.remove("dragover")}));dz.addEventListener("drop",e=>uploadFiles(e.dataTransfer.files));
  $("refreshValidationsBtn").addEventListener("click",async()=>{state.detail.validations=await api(`/api/analyses/${state.analysisId}/validations`);renderValidations();toast("Validation checks refreshed")});
  $$("[data-validation-filter]").forEach(b=>b.addEventListener("click",()=>{state.validationFilter=b.dataset.validationFilter;$$('[data-validation-filter]').forEach(x=>x.classList.toggle("active",x===b));renderValidations()}));
  $("validationList").addEventListener("click",e=>{const b=e.target.closest(".validation-action");if(b)updateValidation(Number(b.dataset.id),b.dataset.status)});
  $$("[data-history-tab]").forEach(b=>b.addEventListener("click",()=>{$$("[data-history-tab]").forEach(x=>x.classList.toggle("active",x===b));$$('[data-history-panel]').forEach(x=>x.classList.toggle("active",x.dataset.historyPanel===b.dataset.historyTab))}));
  $("monthlyTableBody").addEventListener("input",e=>{if(e.target.matches("input[data-field]")){const tr=e.target.closest("tr");const vals=[...tr.querySelectorAll('input[data-field="commerce_revenue"],input[data-field="industry_revenue"],input[data-field="service_revenue"]')].reduce((a,i)=>a+Number(i.value||0),0);tr.querySelector(".row-total").textContent=money(vals,true);}});
}

async function init(){
  wireEvents();
  try{
    await Promise.all([loadBootstrap(),loadGlobal()]);
    await loadAnalysisContext();
    renderRules();
  }catch(e){console.error(e);toast(`Startup error: ${e.message}`);}
}

document.addEventListener("DOMContentLoaded",init);
