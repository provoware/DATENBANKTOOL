const status = document.querySelector("#liveStatus");
const helpButton = document.querySelector("#helpButton");
const helpPanel = document.querySelector("#helpPanel");

async function loadHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error("Health-Check fehlgeschlagen");
    }
    status.innerHTML = `<span aria-hidden="true">●</span> ${data.status.toUpperCase()} · ${data.ampel.toUpperCase()}`;
    status.className = "status-pill status-warning";
  } catch {
    status.innerHTML = '<span aria-hidden="true">●</span> SERVER NICHT ERREICHBAR';
    status.className = "status-pill status-error";
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
