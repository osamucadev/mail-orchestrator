import { api } from "../lib/api";
import { toast } from "../components/toast";

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
            <div class="empty empty--boxed">
              <div class="empty-title">No sent emails yet</div>
              <div class="empty-sub">Send one from Compose or via Swagger, then come back here.</div>
            </div>
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
  let loading = false;

  function setLoading(value) {
    loading = value;
    els.btnRefresh.disabled = loading;
    els.btnLoadMore.disabled = loading || items.length >= total;
  }

  function disableItemButtons(id, value) {
    const card = root.querySelector(`.history-item[data-id="${id}"]`);
    if (!card) return;
    card.querySelectorAll("button").forEach((b) => (b.disabled = value));
  }

  function setStatus(text, kind = "muted") {
    els.status.textContent = text || "";
    els.status.className = `status status--${kind}`;
  }

  function render() {
    if (loading && !items.length) {
      els.list.innerHTML = `
        <div class="skeleton-list">
          ${Array.from({ length: 6 })
            .map(
              () => `
            <div class="skeleton-item">
              <div class="skeleton-emoji"></div>
              <div class="skeleton-lines">
                <div class="skeleton-line"></div>
                <div class="skeleton-line skeleton-line--short"></div>
              </div>
            </div>
          `,
            )
            .join("")}
        </div>`;
      return;
    }

    if (!items.length) {
      els.list.innerHTML = `
      <div class="history" data-role="list">
        <div class="empty empty--boxed">
          <div class="empty-title">No sent emails yet</div>
          <div class="empty-sub">Send one from Compose or via Swagger, then come back here.</div>
        </div>
      </div>`;
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
                  <div class="history-subject">Software Engineer (remote) - Apply</div>
                  <div class="history-meta">
                    <span class="mono">${escapeHtml(e.relative_time)}</span>
                    <span class="dot">•</span>
                    <span class="mono">Sent: ${e.send_count}</span>
                    <span class="mono">to: example@email.com</span>
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
              <button class="btn btn--ghost btn--danger" data-action="delete">Delete</button>
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function loadPage({ reset = false } = {}) {
    setLoading(true);

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
    } finally {
      setLoading(false);
    }
  }

  async function handleCheckReply(id) {
    disableItemButtons(id, true);
    setStatus("Checking reply…", "muted");
    try {
      const result = await api.emails.checkReply(id);
      await loadPage({ reset: true });

      if (result.responded) toast("Reply detected", "ok");
      else toast("No reply found", "muted");
    } catch (err) {
      toast("Reply check failed", "error");
      setStatus(err.message, "error");
    } finally {
      disableItemButtons(id, false);
    }
  }

  async function handleResend(id) {
    disableItemButtons(id, true);
    setStatus("Resending…", "muted");
    try {
      await api.emails.resend(id);
      await loadPage({ reset: true });
      toast("Email resent", "ok");
      setStatus("Resent", "ok");
    } catch (err) {
      toast("Failed to resend", "error");
      setStatus(err.message, "error");
    } finally {
      disableItemButtons(id, false);
    }
  }

  async function handleMark(id, responded) {
    disableItemButtons(id, true);
    setStatus("Updating…", "muted");
    try {
      await api.emails.markResponded(id, responded);
      await loadPage({ reset: true });
      toast(responded ? "Marked as replied" : "Marked as not replied", "ok");
      setStatus("Updated", "ok");
    } catch (err) {
      toast("Failed to update", "error");
      setStatus(err.message, "error");
    } finally {
      disableItemButtons(id, false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this email?")) return;

    disableItemButtons(id, true);
    setStatus("Deleting…", "muted");
    try {
      await api.emails.delete(id);
      await loadPage({ reset: true });
      toast("Email deleted", "ok");
      setStatus("Deleted", "ok");
    } catch (err) {
      toast("Failed to delete", "error");
      setStatus(err.message, "error");
    } finally {
      disableItemButtons(id, false);
    }
  }

  root.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    if (loading) return;

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

    if (action === "delete") {
      handleDelete(parseInt(id));
      return;
    }
  });

  await loadPage({ reset: true });
}
