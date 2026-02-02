import { renderTemplatesPage } from "./templatesPage";
import { renderHistoryPage } from "./historyPage";

function normalizeHash(hash) {
  const h = (hash || "").replace("#", "").trim();
  return h || "compose";
}

export function getRoute() {
  return normalizeHash(window.location.hash);
}

export function renderRoute(root) {
  const route = getRoute();

  if (route === "templates") {
    renderTemplatesPage(root);
    return;
  }

  if (route === "history") {
    renderHistoryPage(root);
    return;
  }

  root.innerHTML = `
    <section id="stack">
      <div class="container">
        <h2 class="section-title">${route[0].toUpperCase()}${route.slice(1)}</h2>

        <div class="stack-cards">
          <div class="stack-card stack-card--core">
            <div class="stack-icon" aria-label="WIP">W</div>
            <div class="stack-content">
              <h3>Work in progress</h3>
              <p>
                This page will be implemented next.
              </p>
              <p class="stack-tech">
                Go to Templates to use the first full CRUD flow.
              </p>
            </div>
          </div>
        </div>

        <div class="stack-closing">
          <p>Local-first now. Deployment-ready later.</p>
        </div>
      </div>
    </section>
  `;
}
