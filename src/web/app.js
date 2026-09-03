const status = document.querySelector("#liveStatus");
const helpButton = document.querySelector("#helpButton");
const helpPanel = document.querySelector("#helpPanel");

function applyHealthStatus(data) {
  const traffic = String(data.ampel || "gelb").toLowerCase();
  const className = traffic === "rot" ? "status-error" : traffic === "grün" ? "status-success" : "status-warning";

  status.innerHTML = `<span aria-hidden="true">●</span> ${String(data.status || "status").toUpperCase()} · ${traffic.toUpperCase()}`;
  status.className = `status-pill ${className}`;
  status.title = String(data.message || "Status des lokalen Tools.");
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const data = await response.json();
    applyHealthStatus(data);
  } catch {
    status.innerHTML = '<span aria-hidden="true">●</span> SERVER NICHT ERREICHBAR';
    status.className = "status-pill status-error";
    status.title = "Der lokale Server antwortet nicht. Starter und Kurzbericht prüfen.";
  }
}

function toggleHelp() {
  const opening = helpPanel.hidden;
  helpPanel.hidden = !opening;
  helpButton.textContent = opening ? "Hilfe schließen" : "Hilfe anzeigen";
  if (opening) {
    helpPanel.focus?.();
  }
}

helpButton.addEventListener("click", toggleHelp);

for (const element of document.querySelectorAll("[data-tip]")) {
  element.setAttribute("aria-label", `${element.textContent.trim()}. ${element.dataset.tip}`);
}

void loadHealth();
