const state = {
  config: null,
  results: null,
  voter: null,
  selections: {},
};

const registerForm = document.getElementById("register-form");
const voteForm = document.getElementById("vote-form");
const registerMessage = document.getElementById("register-message");
const voteMessage = document.getElementById("vote-message");
const registrationStatus = document.getElementById("registration-status");
const voteStatus = document.getElementById("vote-status");
const summaryCards = document.getElementById("summary-cards");
const resultsGrid = document.getElementById("results-grid");
const votePanel = document.getElementById("vote-panel");

function setMessage(node, text, tone = "") {
  node.textContent = text || "";
  node.className = `message ${tone}`.trim();
}

function renderSummary(results, target) {
  target.innerHTML = `
    <article class="stat-card">
      <span>Registrados</span>
      <strong>${results.summary.registered_voters}</strong>
    </article>
    <article class="stat-card">
      <span>Votos emitidos</span>
      <strong>${results.summary.total_votes_cast}</strong>
    </article>
    <article class="stat-card">
      <span>Cargos</span>
      <strong>${results.summary.offices_count}</strong>
    </article>
    <article class="stat-card">
      <span>Fecha objetivo</span>
      <strong>12/04</strong>
    </article>
  `;
}

function renderResults(results, target) {
  target.innerHTML = results.offices
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

function renderVoteForm() {
  voteForm.innerHTML = state.config.offices
    .map(
      (office) => `
        <fieldset class="office-fieldset">
          <legend>${office.title}</legend>
          <p>${office.description}</p>
          <div class="options">
            ${office.candidates
              .map(
                (candidate) => `
                  <label class="option-card">
                    <input
                      type="radio"
                      name="${office.id}"
                      value="${candidate.id}"
                      ${state.selections[office.id] === candidate.id ? "checked" : ""}
                      ${Object.keys(state.selections).length ? "disabled" : ""}
                    >
                    <span class="option-party-line">
                      <span class="party-mark" style="--party-color:${candidate.color}">
                        ${candidate.badge || candidate.short_name.slice(0, 2)}
                      </span>
                      <span>
                        <strong class="option-title">${candidate.short_name || candidate.name}</strong>
                        <small>${candidate.party || ""}</small>
                      </span>
                    </span>
                    <span class="option-list-name">${candidate.list_name || ""}</span>
                  </label>
                `
              )
              .join("")}
          </div>
        </fieldset>
      `
    )
    .join("") + `<button class="primary" type="submit" ${Object.keys(state.selections).length ? "disabled" : ""}>Confirmar votos</button>`;
}

function applyBootstrap(payload) {
  state.config = payload.config;
  state.results = payload.results;
  state.voter = payload.voter;
  state.selections = payload.selections || {};

  document.title = payload.config.title;
  renderSummary(payload.results, summaryCards);
  renderResults(payload.results, resultsGrid);

  if (state.voter) {
    registrationStatus.textContent = `${state.voter.name}`;
    registrationStatus.classList.add("ok");
    votePanel.classList.remove("hidden");
    setMessage(registerMessage, `Registrado como ${state.voter.email}`, "ok");
  }

  if (Object.keys(state.selections).length) {
    voteStatus.textContent = "Voto registrado";
    voteStatus.classList.add("ok");
    setMessage(voteMessage, "Este correo ya emitio su voto.", "ok");
  }

  renderVoteForm();
}

async function fetchBootstrap() {
  const response = await fetch("/api/bootstrap");
  const payload = await response.json();
  applyBootstrap(payload);
}

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    name: document.getElementById("name").value,
    email: document.getElementById("email").value,
  };

  const response = await fetch("/api/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();

  if (!response.ok) {
    setMessage(registerMessage, payload.error || "No se pudo registrar.", "error");
    return;
  }

  state.voter = payload.voter;
  state.selections = payload.selections || {};
  registrationStatus.textContent = state.voter.name;
  registrationStatus.classList.add("ok");
  votePanel.classList.remove("hidden");
  renderVoteForm();
  setMessage(registerMessage, "Registro completado. Ahora elige tus opciones.", "ok");
});

voteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const selections = {};

  for (const office of state.config.offices) {
    const selected = voteForm.querySelector(`input[name="${office.id}"]:checked`);
    if (!selected) {
      setMessage(voteMessage, `Falta seleccionar una opcion en ${office.title}.`, "error");
      return;
    }
    selections[office.id] = selected.value;
  }

  const response = await fetch("/api/vote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selections }),
  });
  const payload = await response.json();

  if (!response.ok) {
    setMessage(voteMessage, payload.error || "No se pudo registrar el voto.", "error");
    return;
  }

  state.selections = selections;
  voteStatus.textContent = "Voto registrado";
  voteStatus.classList.add("ok");
  setMessage(voteMessage, "Tu voto fue registrado correctamente.", "ok");
  renderVoteForm();
  renderSummary(payload.results, summaryCards);
  renderResults(payload.results, resultsGrid);
});

function connectStream() {
  const source = new EventSource("/api/stream");
  source.addEventListener("snapshot", (event) => {
    const results = JSON.parse(event.data);
    state.results = results;
    renderSummary(results, summaryCards);
    renderResults(results, resultsGrid);
  });
}

fetchBootstrap().then(connectStream);
