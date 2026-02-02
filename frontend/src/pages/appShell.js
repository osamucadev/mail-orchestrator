export function renderAppShell(root) {
  root.innerHTML = `
    <header class="topbar">
      <div class="container topbar-inner">
        <div class="brand">
          <span class="brand-mark">MO</span>
          <span class="brand-name">Mail Orchestrator</span>
        </div>

        <nav class="nav">
          <a class="nav-link is-active" href="#compose">Compose</a>
          <a class="nav-link" href="#history">History</a>
          <a class="nav-link" href="#templates">Templates</a>
          <a class="nav-link" href="#settings">Settings</a>
        </nav>
      </div>
    </header>

    <main class="page">
      <section id="stack">
        <div class="container">
          <h2 class="section-title">Mail Orchestrator</h2>

          <div class="stack-cards">
            <div class="stack-card stack-card--core">
              <div class="stack-icon" aria-label="Compose">C</div>
              <div class="stack-content">
                <h3>Compose with intent</h3>
                <p>
                  Write emails fast with a text and HTML editor, preview, inline images,
                  and attachments managed outside the editor.
                </p>
                <p class="stack-tech">
                  Text, HTML, Preview, clipboard images, attachments, templates
                </p>
              </div>
            </div>

            <div class="stack-card">
              <div class="stack-icon" aria-label="History">H</div>
              <div class="stack-content">
                <h3>Track what was sent</h3>
                <p>
                  Local history with relative time, status emojis, reply checks and manual reply marking.
                </p>
                <p class="stack-tech">
                  SQLite, reply checks, resend, manual replied
                </p>
              </div>
            </div>

            <div class="stack-card">
              <div class="stack-icon" aria-label="Templates">T</div>
              <div class="stack-content">
                <h3>Templates with placeholders</h3>
                <p>
                  Create templates with unlimited placeholders and let the UI generate the input fields automatically.
                </p>
                <p class="stack-tech">
                  Placeholder parsing, dynamic forms, substitution on send
                </p>
              </div>
            </div>
          </div>

          <div class="stack-closing">
            <p>
              Local-first now. Deployment-ready later. The criteria stays.
            </p>
          </div>
        </div>
      </section>
    </main>
  `
}
