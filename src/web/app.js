const status = document.querySelector("#liveStatus");
const helpButton = document.querySelector("#helpButton");
const helpPanel = document.querySelector("#helpPanel");
const progressValue = document.querySelector("#progressValue");
const progressBar = document.querySelector("#progressBar");
const progressBlocks = document.querySelector("#progressBlocks");
const footer = document.querySelector("#footerText");

let messages = {};
let projectMeta = {};

function text(key, fallback = key) {
  return messages[key] ?? fallback;
}

async function loadStaticConfig() {
  const locale = document.documentElement.lang || "de";
  const [localeResponse, metaResponse] = await Promise.all([
    fetch(`/i18n/${locale}.json`, { cache: "no-store" }),
    fetch("/api/project/meta", { cache: "no-store" }),
  ]);
  const catalog = await localeResponse.json();
  projectMeta = await metaResponse.json();
  messages = catalog.messages ?? {};
  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = text(element.dataset.i18n, element.textContent);
  }
  for (const element of document.querySelectorAll("[data-i18n-aria]")) {
    element.setAttribute(
      "aria-label",
      text(element.dataset.i18nAria, element.getAttribute("aria-label") || ""),
    );
  }
  document.title = text("page.title", document.title);
  helpButton.title = text("help.tip", "");
  renderProjectMeta();
}

function renderProgress(percent) {
  const safe = Math.max(0, Math.min(100, Number(percent) || 0));
  const filled = Math.round(safe / 10);
  progressValue.textContent = `${safe} %`;
  progressBar.setAttribute("aria-valuenow", String(safe));
  progressBar.querySelector("span").style.width = `${safe}%`;
  progressBlocks.textContent = `[${"■".repeat(filled)}${"□".repeat(10 - filled)}]`;
}

function renderProjectMeta() {
  const product = projectMeta.product ?? {};
  renderProgress(product.progress_percent);
  footer.textContent = `PROVOWARE DATENBANKTOOL · ${product.version || "–"} · ${text("footer.suffix", "lokaler Datenkern")}`;
}

function applyHealthStatus(data) {
  const traffic = String(data.ampel || "gelb").toLowerCase();
  const className =
    traffic === "rot" ? "status-error" : traffic === "grün" ? "status-success" : "status-warning";
  const statusKey = data.status_message_key || projectMeta.product?.status_message_key;
  const label = text(statusKey, data.status || "status");
  status.innerHTML = `<span aria-hidden="true">●</span> ${String(label).toUpperCase()} · ${traffic.toUpperCase()}`;
  status.className = `status-pill ${className}`;
  status.title = String(data.message || text("status.default_tip", "Status des lokalen Tools."));
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const data = await response.json();
    applyHealthStatus(data);
  } catch {
    status.innerHTML = `<span aria-hidden="true">●</span> ${text("status.unreachable", "SERVER NICHT ERREICHBAR")}`;
    status.className = "status-pill status-error";
    status.title = text("status.unreachable_tip", "Der lokale Server antwortet nicht.");
  }
}

function toggleHelp() {
  const opening = helpPanel.hidden;
  helpPanel.hidden = !opening;
  helpButton.textContent = text(opening ? "help.close" : "help.open", helpButton.textContent);
  if (opening) helpPanel.focus?.();
}

helpButton.addEventListener("click", toggleHelp);
await loadStaticConfig();
await loadHealth();
