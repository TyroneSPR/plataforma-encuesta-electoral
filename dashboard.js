const summaryCards = document.getElementById("dashboard-summary-cards");
const resultsGrid = document.getElementById("dashboard-results-grid");

function renderSummary(results) {
  summaryCards.innerHTML = `
    <article class="stat-card">
      <span>Registrados</span>
      <strong>${results.summary.registered_voters}</strong>
    </article>
    <article class="stat-card">
      <span>Votos emitidos</span>
      <strong>${results.summary.total_votes_cast}</strong>
    </article>
    <article class="stat-card">
      <span>Ultima actualizacion</span>
      <strong>${new Date(results.updated_at).toLocaleTimeString("es-PE")}</strong>
    </article>
    <article class="stat-card">
      <span>Secciones</span>
      <strong>${results.summary.offices_count}</strong>
    </article>
  `;
}

function renderResults(results) {
  resultsGrid.innerHTML = results.offices
    .map(
      (office) => `
        <article class="office-card">
          <div class="office-head">
            <div>
              <h3>${office.title}</h3>
              <p>${office.description}</p>
            </div>
            <span>${office.total_votes} votos</span>
          </div>
          <div class="candidate-list">
            ${office.candidates
              .map(
                (candidate) => `
                  <div class="candidate-row">
                    <div class="candidate-meta">
                      <div class="party-mark" style="--party-color:${candidate.color}">
                        ${candidate.badge || candidate.short_name.slice(0, 2)}
                      </div>
                      <div>
                        <strong>${candidate.short_name || candidate.name}</strong>
                        <span>${candidate.list_name || candidate.party || ""}</span>
                      </div>
                    </div>
                    <div class="bar-wrap">
                      <div class="bar" style="width:${candidate.percentage}%; --party-color:${candidate.color}"></div>
                    </div>
                    <div class="candidate-score">
                      <strong>${candidate.votes}</strong>
                      <span>${candidate.percentage}%</span>
                    </div>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `
    )
    .join("");
}

async function initDashboard() {
  const response = await fetch("/api/results");
  const results = await response.json();
  renderSummary(results);
  renderResults(results);

  const source = new EventSource("/api/stream");
  source.addEventListener("snapshot", (event) => {
    const payload = JSON.parse(event.data);
    renderSummary(payload);
    renderResults(payload);
  });
}

initDashboard();
