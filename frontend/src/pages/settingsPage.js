import { api } from "../lib/api";

function clampInt(value, fallback = 0) {
  const n = Number.parseInt(value, 10);
  if (Number.isNaN(n)) return fallback;
  return Math.max(0, n);
}

function emojiForMinutes(minutes, t) {
  if (minutes <= t.t_white_minutes) return "⚪";
  if (minutes <= t.t_blue_minutes) return "🔵";
  if (minutes <= t.t_yellow_minutes) return "🟡";
  return "🔴";
}

export async function renderSettingsPage(root) {
  root.innerHTML = `
    <section class="page-shell">
      <div class="container">
        <div class="page-head">
          <div>
            <h2 class="page-title">Settings</h2>
            <p class="page-subtitle">
              Configure time thresholds (in minutes) used to compute the status emoji in History.
              Green is always reserved for replied.
            </p>
          </div>

          <div class="page-actions">
            <button class="btn" data-action="save" disabled>Save</button>
            <button class="btn btn--ghost" data-action="reload">Reload</button>
          </div>
        </div>

        <div class="grid grid--settings">
          <section class="panel panel--main">
            <div class="panel-head">
              <h3 class="panel-title">Emoji thresholds</h3>
              <div class="panel-actions">
                <span class="status status--muted" data-role="status"></span>
              </div>
            </div>

            <form class="form" data-role="form">
              <div class="cols cols--4">
                <label class="field">
                  <span class="label">⚪ White (newest)</span>
                  <input class="input input--mono" name="t_white_minutes" type="number" min="0" step="1" />
                  <span class="hint">Up to this many minutes ago</span>
                </label>

                <label class="field">
                  <span class="label">🔵 Blue</span>
                  <input class="input input--mono" name="t_blue_minutes" type="number" min="0" step="1" />
                  <span class="hint">After white, up to this many minutes ago</span>
                </label>

                <label class="field">
                  <span class="label">🟡 Yellow</span>
                  <input class="input input--mono" name="t_yellow_minutes" type="number" min="0" step="1" />
                  <span class="hint">After blue, up to this many minutes ago</span>
                </label>

                <label class="field">
                  <span class="label">🔴 Red (oldest)</span>
                  <input class="input input--mono" name="t_red_minutes" type="number" min="0" step="1" />
                  <span class="hint">After yellow, red is used</span>
                </label>
              </div>

              <div class="panel panel--inner">
                <div class="panel-head">
                  <h3 class="panel-title">Preview</h3>
                </div>

                <div class="preview-grid" data-role="preview"></div>

                <p class="note">
                  Replied is always <span class="mono">🟢</span>, regardless of time.
                </p>
              </div>
            </form>
          </section>

          <aside class="panel">
            <div class="panel-head">
              <h3 class="panel-title">Rules</h3>
            </div>

            <ul class="bullets">
              <li>Thresholds are configured in minutes.</li>
              <li>Status is computed from the time elapsed since <code>sent_at</code>.</li>
              <li>Emoji order is fixed: <code>⚪</code>, <code>🔵</code>, <code>🟡</code>, <code>🔴</code>.</li>
              <li><code>🟢</code> is reserved for replied.</li>
            </ul>
          </aside>
        </div>
      </div>
    </section>
  `;

  const els = {
    status: root.querySelector('[data-role="status"]'),
    form: root.querySelector('[data-role="form"]'),
    preview: root.querySelector('[data-role="preview"]'),
    btnSave: root.querySelector('[data-action="save"]'),
    btnReload: root.querySelector('[data-action="reload"]'),
  };

  let current = null;
  let dirty = false;

  function setStatus(text, kind = "muted") {
    els.status.textContent = text || "";
    els.status.className = `status status--${kind}`;
  }

  function setDirty(value) {
    dirty = value;
    els.btnSave.disabled = !dirty;
  }

  function readForm() {
    return {
      t_white_minutes: clampInt(els.form.t_white_minutes.value, 0),
      t_blue_minutes: clampInt(els.form.t_blue_minutes.value, 0),
      t_yellow_minutes: clampInt(els.form.t_yellow_minutes.value, 0),
      t_red_minutes: clampInt(els.form.t_red_minutes.value, 0),
    };
  }

  function writeForm(data) {
    els.form.t_white_minutes.value = data.t_white_minutes;
    els.form.t_blue_minutes.value = data.t_blue_minutes;
    els.form.t_yellow_minutes.value = data.t_yellow_minutes;
    els.form.t_red_minutes.value = data.t_red_minutes;
  }

  function validate(t) {
    const ok =
      t.t_white_minutes <= t.t_blue_minutes &&
      t.t_blue_minutes <= t.t_yellow_minutes &&
      t.t_yellow_minutes <= t.t_red_minutes;

    return ok
      ? { ok: true, message: "Ready" }
      : {
          ok: false,
          message:
            "Thresholds must be non-decreasing: white <= blue <= yellow <= red",
        };
  }

  function renderPreview(t) {
    const samples = [
      { label: "just sent", minutes: 0 },
      { label: "15 minutes ago", minutes: 15 },
      { label: "1 hour ago", minutes: 60 },
      { label: "6 hours ago", minutes: 360 },
      { label: "1 day ago", minutes: 1440 },
      { label: "3 days ago", minutes: 4320 },
    ];

    els.preview.innerHTML = samples
      .map((s) => {
        const emoji = emojiForMinutes(s.minutes, t);
        return `
          <div class="preview-card">
            <div class="preview-emoji">${emoji}</div>
            <div class="preview-text">
              <div class="preview-title">${s.label}</div>
              <div class="preview-sub mono">${s.minutes} minutes</div>
            </div>
          </div>
        `;
      })
      .join("");
  }

  async function load() {
    setStatus("Loading…", "muted");
    try {
      const data = await api.settings.get();
      current = {
        t_white_minutes: data.t_white_minutes,
        t_blue_minutes: data.t_blue_minutes,
        t_yellow_minutes: data.t_yellow_minutes,
        t_red_minutes: data.t_red_minutes,
      };
      writeForm(current);
      renderPreview(current);
      setDirty(false);
      setStatus("Ready", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  async function save() {
    const next = readForm();
    const v = validate(next);
    if (!v.ok) {
      setStatus(v.message, "error");
      return;
    }

    setStatus("Saving…", "muted");
    try {
      const saved = await api.settings.update(next);
      current = {
        t_white_minutes: saved.t_white_minutes,
        t_blue_minutes: saved.t_blue_minutes,
        t_yellow_minutes: saved.t_yellow_minutes,
        t_red_minutes: saved.t_red_minutes,
      };
      writeForm(current);
      renderPreview(current);
      setDirty(false);
      setStatus("Saved", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  els.btnSave.addEventListener("click", (e) => {
    e.preventDefault();
    save();
  });

  els.btnReload.addEventListener("click", (e) => {
    e.preventDefault();
    load();
  });

  els.form.addEventListener("input", () => {
    const next = readForm();
    renderPreview(next);

    if (!current) {
      setDirty(true);
      return;
    }

    const changed =
      next.t_white_minutes !== current.t_white_minutes ||
      next.t_blue_minutes !== current.t_blue_minutes ||
      next.t_yellow_minutes !== current.t_yellow_minutes ||
      next.t_red_minutes !== current.t_red_minutes;

    setDirty(changed);

    const v = validate(next);
    if (!v.ok) setStatus(v.message, "error");
    else setStatus("Ready", dirty ? "muted" : "ok");
  });

  await load();
}
