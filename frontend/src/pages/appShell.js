import { getRoute, renderRoute } from "./router";

function setActiveNav(root) {
  const route = getRoute();
  const links = root.querySelectorAll(".nav-link");
  for (const a of links) {
    const href = a.getAttribute("href") || "";
    const key = href.replace("#", "");
    a.classList.toggle("is-active", key === route);
  }
}

export function renderAppShell(root) {
  root.innerHTML = `
    <header class="topbar">
      <div class="container topbar-inner">
        <div class="brand">
          <span class="brand-mark">MO</span>
          <span class="brand-name">Mail Orchestrator</span>
        </div>

        <nav class="nav">
          <a class="nav-link" href="#compose">Compose</a>
          <a class="nav-link" href="#history">History</a>
          <a class="nav-link" href="#templates">Templates</a>
          <a class="nav-link" href="#settings">Settings</a>
        </nav>
      </div>
    </header>

    <main class="page" data-role="page"></main>
  `;

  const page = root.querySelector('[data-role="page"]');

  function run() {
    setActiveNav(root);
    renderRoute(page);
  }

  window.addEventListener("hashchange", run);
  run();
}
