import { api } from "../lib/api";

function escapeHtml(s) {
  return (s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export async function renderHistoryPage(root) {
  root.innerHTML = `
    <section class="page-shell">
      <div class="container">
        <div class="page-head">
          <div>
            <h2 class="page-title">History</h2>
            <p class="page-subtitle">Local sent emails with relative time, status emojis, and manual actions.</p>
          </div>

          <div class="page-actions">
            <button class="btn btn--ghost" data-action="refresh">Refresh</button>
          </div>
        </div>

        <section class="panel panel--main">
          <div class="panel-head">
            <h3 class="panel-title">Sent</h3>
            <div class="panel-actions">
              <span class="status status--muted" data-role="status"></span>
            </div>
          </div>

          <div class="history" data-role="list">
            <div class="empty">No emails yet. Send one via Swagger or wait for Compose.</div>
          </div>

          <div class="history-foot">
            <button class="btn btn--ghost" data-action="load-more">Load more</button>
          </div>
        </section>
      </div>
    </section>
  `;

  const els = {
    status: root.querySelector('[data-role="status"]'),
    list: root.querySelector('[data-role="list"]'),
    btnRefresh: root.querySelector('[data-action="refresh"]'),
    btnLoadMore: root.querySelector('[data-action="load-more"]'),
  };

  let limit = 50;
  let offset = 0;
  let total = 0;
  let items = [];

  function setStatus(text, kind = "muted") {
    els.status.textContent = text || "";
    els.status.className = `status status--${kind}`;
  }

  function render() {
    if (!items.length) {
      els.list.innerHTML = `<div class="empty">No emails yet. Send one via Swagger or wait for Compose.</div>`;
      return;
    }

    els.list.innerHTML = items
      .map((e) => {
        const respondedBadge = e.responded
          ? `<span class="pill pill--ok">Replied</span>`
          : `<span class="pill">Not replied</span>`;

        return `
          <article class="history-item" data-id="${e.id}">
            <div class="history-main">
              <div class="history-emoji" aria-label="status">${escapeHtml(e.status_emoji)}</div>

              <div class="history-content">
                <div class="history-top">
                  <div class="history-subject">${escapeHtml(e.subject)}</div>
                  <div class="history-meta">
                    <span class="mono">${escapeHtml(e.relative_time)}</span>
                    <span class="dot">•</span>
                    <span class="mono">to: ${escapeHtml(e.to)}</span>
                  </div>
                </div>

                <div class="history-bottom">
                  ${respondedBadge}
                </div>
              </div>
            </div>

            <div class="history-actions">
              <div class="history-actions">
              <button class="btn btn--ghost" data-action="check-reply">Check reply</button>
              <button class="btn btn--ghost" data-action="resend">Resend</button>
              ${
                e.responded
                  ? `<button class="btn btn--ghost" data-action="mark-unreplied">Mark not replied</button>`
                  : `<button class="btn" data-action="mark-replied">Mark replied</button>`
              }
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function loadPage({ reset = false } = {}) {
    if (reset) {
      offset = 0;
      items = [];
      total = 0;
    }

    setStatus("Loading…", "muted");
    try {
      const data = await api.emails.history(limit, offset);
      total = data.total || 0;

      if (reset) items = data.items || [];
      else items = items.concat(data.items || []);

      offset = items.length;
      render();

      const shown = items.length;
      setStatus(`${shown} shown of ${total}`, "ok");

      els.btnLoadMore.disabled = shown >= total;
      els.btnLoadMore.textContent = shown >= total ? "No more" : "Load more";
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  async function handleCheckReply(id) {
    const btns = root.querySelectorAll(`.history-item[data-id="${id}"] button`);
    btns.forEach((b) => (b.disabled = true));
    setStatus("Checking reply…", "muted");
    try {
      const result = await api.emails.checkReply(id);
      await loadPage({ reset: true });

      if (result.responded) {
        setStatus("Reply detected", "ok");
      } else {
        setStatus("No reply found", "muted");
      }
    } catch (err) {
      setStatus(err.message, "error");
    } finally {
      btns.forEach((b) => (b.disabled = false));
    }
  }

  async function handleResend(id) {
    setStatus("Resending…", "muted");
    try {
      await api.emails.resend(id);
      await loadPage({ reset: true });
      setStatus("Resent", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  async function handleMark(id, responded) {
    setStatus("Updating…", "muted");
    try {
      await api.emails.markResponded(id, responded);
      await loadPage({ reset: true });
      setStatus("Updated", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  root.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.getAttribute("data-action");

    if (action === "refresh") {
      loadPage({ reset: true });
      return;
    }

    if (action === "load-more") {
      loadPage({ reset: false });
      return;
    }

    const card = btn.closest(".history-item");
    if (!card) return;
    const id = card.getAttribute("data-id");
    if (!id) return;

    if (action === "check-reply") {
      handleCheckReply(id);
      return;
    }

    if (action === "resend") {
      handleResend(id);
      return;
    }

    if (action === "mark-replied") {
      handleMark(id, true);
      return;
    }

    if (action === "mark-unreplied") {
      handleMark(id, false);
    }
  });

  await loadPage({ reset: true });
}
