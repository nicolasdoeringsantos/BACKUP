const STATUS_LABELS = {
  success: "Atualizado",
  warning: "Aviso",
  error: "Erro",
  nomon: "Sem monitoramento",
};

const STAT_CARDS = [
  { key: "total", label: "Total de tarefas", color: "var(--ink)" },
  { key: "error", label: "Erro", color: "var(--error)" },
  { key: "warning", label: "Aviso", color: "var(--warning)" },
  { key: "stale", label: "Desatualizado", color: "var(--stale)" },
  { key: "nomon", label: "Sem monitoramento", color: "var(--nomon)" },
  { key: "success", label: "Atualizado", color: "var(--success)" },
];

const FILTER_KEY_MAP = {
  all: null,
  error: "error",
  warning: "warning",
  success: "success",
  nomon: "nomon",
  stale: "__stale__",
};

let state = {
  items: [],
  summary: {},
  filter: "all",
  search: "",
  sortKey: "client_name",
  sortDir: 1,
};

async function loadData(showToastOnError = true) {
  setLoadingDot();
  try {
    const res = await fetch("/api/data");
    const data = await res.json();
    state.items = data.items || [];
    state.summary = data.summary || {};
    renderSummary();
    renderChart();
    renderTable();
    renderLastUpdate(data.last_fetch);
    setDot(true);
 } catch (e) {
    console.error("Erro ao carregar painel:", e);
    setDot(false);
    if (showToastOnError) showToast("Erro ao carregar dados do painel", true);
  }
}

function renderChart() {
  const donutArc = document.getElementById("donutArc");
  if (!donutArc) return; // seção do gráfico não está no HTML ainda

  const total = state.items.length;
  const correct = state.items.filter(i => i.status === "success" && !i.is_stale).length;
  const incorrect = total - correct;
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0;

  document.getElementById("donutPercent").textContent = pct + "%";
  document.getElementById("legendCorrectCount").textContent = correct;
  document.getElementById("legendIncorrectCount").textContent = incorrect;

  const circumference = 2 * Math.PI * 50;
  donutArc.setAttribute("stroke-dasharray", `${(pct / 100) * circumference} ${circumference}`);
  donutArc.setAttribute("stroke", pct >= 70 ? "var(--success)" : pct >= 40 ? "var(--warning)" : "var(--error)");
}
function setLoadingDot() {
  const dot = document.getElementById("statusDot");
  dot.className = "dot loading";
}

function setDot(ok) {
  const dot = document.getElementById("statusDot");
  dot.className = "dot " + (ok ? "ok" : "bad");
}

function renderLastUpdate(lastFetch) {
  const el = document.getElementById("lastUpdateText");
  if (!lastFetch) {
    el.textContent = "ainda sem coleta";
    return;
  }
  const dt = new Date(lastFetch.fetched_at);
  const formatted = dt.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  el.textContent = (lastFetch.success ? "Atualizado " : "Falhou em ") + formatted;
}

function renderSummary() {
  const grid = document.getElementById("summaryGrid");
  grid.innerHTML = STAT_CARDS.map(card => `
    <div class="stat-card ${state.filter === card.key ? 'active' : ''}"
         style="--card-color:${card.color}"
         data-filter="${card.key}">
      <div class="stat-label">${card.label}</div>
      <div class="stat-value">${state.summary[card.key] ?? 0}</div>
    </div>
  `).join("");

  grid.querySelectorAll(".stat-card").forEach(el => {
    el.addEventListener("click", () => setFilter(el.dataset.filter));
  });
}

function setFilter(key) {
  state.filter = key;
  document.querySelectorAll(".tab").forEach(t => {
    t.classList.toggle("active", t.dataset.filter === key);
  });
  renderSummary();
  renderTable();
}

function matchesFilter(item) {
  const f = FILTER_KEY_MAP[state.filter];
  if (state.filter === "all") return true;
  if (f === "__stale__") return item.is_stale;
  return item.status === f;
}

function matchesSearch(item) {
  if (!state.search) return true;
  const q = state.search.toLowerCase();
  return (item.client_name || "").toLowerCase().includes(q)
      || (item.backup_set_name || "").toLowerCase().includes(q)
      || (item.login_name || "").toLowerCase().includes(q);
}

function formatDate(value) {
  if (!value) return "—";
  const dt = new Date(value);
  if (isNaN(dt)) return value;
  return dt.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function renderTable() {
  let rows = state.items.filter(matchesFilter).filter(matchesSearch);

  rows.sort((a, b) => {
    const av = (a[state.sortKey] || "").toString();
    const bv = (b[state.sortKey] || "").toString();
    return av.localeCompare(bv) * state.sortDir;
  });

  const tbody = document.getElementById("tableBody");
  const emptyState = document.getElementById("emptyState");

  if (rows.length === 0) {
    tbody.innerHTML = "";
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";

  tbody.innerHTML = rows.map(item => `
    <tr>
      <td class="client-name">${escapeHtml(item.client_name || "—")}</td>
      <td class="set-name">${escapeHtml(item.backup_set_name || item.login_name || "—")}</td>
      <td>
        <span class="badge ${item.status}">${STATUS_LABELS[item.status] || item.status || "—"}</span>
        ${item.is_stale ? `<span class="badge stale" style="margin-left:5px;">Desatualizado</span>` : ""}
      </td>
      <td class="date-cell">${formatDate(item.last_backup_job_date)}</td>
      <td class="date-cell ${item.is_stale ? 'stale' : ''}">${formatDate(item.last_success_backup_job_date)}</td>
      <td class="link-cell">
        ${item.last_backup_job_url
          ? `<a href="${escapeAttr(item.last_backup_job_url)}" target="_blank" rel="noopener">Ver relatório →</a>`
          : `<span>—</span>`}
      </td>
    </tr>
  `).join("");
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, s => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[s]));
}
function escapeAttr(str) { return escapeHtml(str); }

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = "toast show" + (isError ? " error" : "");
  setTimeout(() => { toast.className = "toast"; }, 3200);
}

async function manualRefresh() {
  const btn = document.getElementById("refreshBtn");
  btn.classList.add("spinning");
  btn.disabled = true;
  try {
    const res = await fetch("/api/refresh", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      await loadData();
    } else {
      showToast(data.message, true);
    }
  } catch (e) {
    showToast("Erro ao atualizar", true);
  } finally {
    btn.classList.remove("spinning");
    btn.disabled = false;
  }
}

// ---------- Event bindings ----------
document.getElementById("refreshBtn").addEventListener("click", manualRefresh);

document.getElementById("searchInput").addEventListener("input", (e) => {
  state.search = e.target.value;
  renderTable();
});

document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => setFilter(tab.dataset.filter));
});

document.querySelectorAll("thead th[data-sort]").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.sort;
    if (state.sortKey === key) {
      state.sortDir *= -1;
    } else {
      state.sortKey = key;
      state.sortDir = 1;
    }
    renderTable();
  });
});

// ---------- Init ----------
loadData();
setInterval(() => loadData(false), 60 * 1000); // refresca a tela a cada 1 min (lê o que já está salvo)
