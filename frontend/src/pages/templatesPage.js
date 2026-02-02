import { api } from "../lib/api";

const emptyTemplate = () => ({
  id: null,
  name: "",
  subject_template: "",
  body_text_template: "",
  body_html_template: "",
});

function escapeHtml(s) {
  return (s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pick(obj, keys) {
  const out = {};
  for (const k of keys) out[k] = obj[k] ?? null;
  return out;
}

export async function renderTemplatesPage(root) {
  root.innerHTML = `
    <section class="page-shell">
      <div class="container">
        <div class="page-head">
          <div>
            <h2 class="page-title">Templates</h2>
            <p class="page-subtitle">Create templates with placeholders and let the backend detect fields automatically.</p>
          </div>

          <div class="page-actions">
            <button class="btn" data-action="new">New template</button>
            <button class="btn btn--ghost" data-action="refresh">Refresh</button>
          </div>
        </div>

        <div class="grid">
          <aside class="panel">
            <div class="panel-head">
              <h3 class="panel-title">Saved templates</h3>
              <span class="badge" data-role="count">0</span>
            </div>

            <div class="list" data-role="list">
              <div class="empty">No templates yet.</div>
            </div>
          </aside>

          <section class="panel panel--main">
            <div class="panel-head">
              <h3 class="panel-title">Editor</h3>
              <div class="panel-actions">
                <span class="status" data-role="status"></span>
                <button class="btn btn--danger btn--ghost" data-action="delete" disabled>Delete</button>
                <button class="btn" data-action="save" disabled>Save</button>
              </div>
            </div>

            <form class="form" data-role="form">
              <label class="field">
                <span class="label">Name</span>
                <input class="input" name="name" placeholder="Recruiter intro" />
              </label>

              <label class="field">
                <span class="label">Subject template</span>
                <input class="input" name="subject_template" placeholder="Hello {{name}} about {{role}}" />
              </label>

              <div class="cols">
                <label class="field">
                  <span class="label">Body text template</span>
                  <textarea class="textarea" name="body_text_template" rows="10" placeholder="Hi {{name}},&#10;I saw the {{role}} role at {{company}}."></textarea>
                </label>

                <label class="field">
                  <span class="label">Body HTML template</span>
                  <textarea class="textarea textarea--mono" name="body_html_template" rows="10" placeholder="<p>Hi {{name}},</p>"></textarea>
                </label>
              </div>

              <div class="split">
                <div class="panel panel--inner">
                  <div class="panel-head">
                    <h3 class="panel-title">Detected placeholders</h3>
                    <button class="btn btn--ghost" type="button" data-action="load-placeholders" disabled>Load</button>
                  </div>
                  <div class="chips" data-role="placeholders">
                    <div class="empty">Save the template to detect placeholders.</div>
                  </div>
                </div>

                <div class="panel panel--inner">
                  <div class="panel-head">
                    <h3 class="panel-title">Tips</h3>
                  </div>
                  <ul class="bullets">
                    <li>Use placeholders like <code>{{name}}</code>, <code>{{company}}</code>, <code>{{role}}</code>.</li>
                    <li>Placeholders are detected from subject, text, and HTML.</li>
                    <li>Order follows first appearance.</li>
                  </ul>
                </div>
              </div>
            </form>
          </section>
        </div>
      </div>
    </section>
  `;

  const els = {
    list: root.querySelector('[data-role="list"]'),
    count: root.querySelector('[data-role="count"]'),
    form: root.querySelector('[data-role="form"]'),
    status: root.querySelector('[data-role="status"]'),
    placeholders: root.querySelector('[data-role="placeholders"]'),
    btnSave: root.querySelector('[data-action="save"]'),
    btnDelete: root.querySelector('[data-action="delete"]'),
    btnNew: root.querySelector('[data-action="new"]'),
    btnRefresh: root.querySelector('[data-action="refresh"]'),
    btnLoadPlaceholders: root.querySelector(
      '[data-action="load-placeholders"]',
    ),
  };

  let templates = [];
  let selected = emptyTemplate();
  let dirty = false;

  function setStatus(text, kind = "muted") {
    els.status.textContent = text || "";
    els.status.className = `status status--${kind}`;
  }

  function setDirty(value) {
    dirty = value;
    els.btnSave.disabled = !dirty;
  }

  function setSelected(template) {
    selected = { ...template };
    dirty = false;

    els.form.name.value = selected.name || "";
    els.form.subject_template.value = selected.subject_template || "";
    els.form.body_text_template.value = selected.body_text_template || "";
    els.form.body_html_template.value = selected.body_html_template || "";

    els.btnDelete.disabled = !selected.id;
    els.btnLoadPlaceholders.disabled = !selected.id;
    els.btnSave.disabled = true;

    els.placeholders.innerHTML = `<div class="empty">Save the template to detect placeholders.</div>`;
    setStatus(
      selected.id ? `Editing #${selected.id}` : "Creating new template",
      "muted",
    );
  }

  function readForm() {
    return {
      name: els.form.name.value.trim(),
      subject_template: els.form.subject_template.value || null,
      body_text_template: els.form.body_text_template.value || null,
      body_html_template: els.form.body_html_template.value || null,
    };
  }

  function renderList() {
    els.count.textContent = String(templates.length);

    if (!templates.length) {
      els.list.innerHTML = `<div class="empty">No templates yet.</div>`;
      return;
    }

    const items = templates
      .map((t) => {
        const isActive = selected?.id === t.id;
        return `
          <button class="list-item ${isActive ? "is-active" : ""}" type="button" data-id="${t.id}">
            <div class="list-title">${escapeHtml(t.name)}</div>
            <div class="list-sub">${escapeHtml(t.subject_template || "No subject")}</div>
          </button>
        `;
      })
      .join("");

    els.list.innerHTML = items;
  }

  async function loadTemplates() {
    setStatus("Loading templates…", "muted");
    try {
      templates = await api.templates.list();
      renderList();

      if (selected.id) {
        const stillExists = templates.find((t) => t.id === selected.id);
        if (!stillExists) setSelected(emptyTemplate());
      }

      setStatus("Ready", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  async function loadPlaceholders() {
    if (!selected.id) return;
    setStatus("Loading placeholders…", "muted");

    try {
      const items = await api.templates.placeholders(selected.id);
      if (!items.length) {
        els.placeholders.innerHTML = `<div class="empty">No placeholders found.</div>`;
      } else {
        els.placeholders.innerHTML = items
          .map(
            (p) =>
              `<span class="chip"><code>{{${escapeHtml(p.key)}}}</code><span class="chip-label">${escapeHtml(p.label)}</span></span>`,
          )
          .join("");
      }
      setStatus("Ready", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  async function saveTemplate() {
    const payload = readForm();
    if (!payload.name) {
      setStatus("Name is required.", "error");
      return;
    }

    setStatus("Saving…", "muted");

    try {
      if (selected.id) {
        const updated = await api.templates.update(selected.id, payload);
        selected = updated;
        setDirty(false);
        setStatus("Saved", "ok");
      } else {
        const created = await api.templates.create(payload);
        selected = created;
        setDirty(false);
        setStatus("Created", "ok");
      }

      await loadTemplates();
      setSelected(selected);
      await loadPlaceholders();
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  async function deleteSelected() {
    if (!selected.id) return;

    const ok = confirm("Delete this template?");
    if (!ok) return;

    setStatus("Deleting…", "muted");

    try {
      await api.templates.remove(selected.id);
      setSelected(emptyTemplate());
      await loadTemplates();
      setStatus("Deleted", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  root.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.getAttribute("data-action");
    if (action === "new") {
      setSelected(emptyTemplate());
      return;
    }
    if (action === "refresh") {
      loadTemplates();
      return;
    }
    if (action === "save") {
      saveTemplate();
      return;
    }
    if (action === "delete") {
      deleteSelected();
      return;
    }
    if (action === "load-placeholders") {
      loadPlaceholders();
      return;
    }

    const id = btn.getAttribute("data-id");
    if (id) {
      const found = templates.find((t) => String(t.id) === String(id));
      if (found) setSelected(found);
    }
  });

  els.form.addEventListener("input", () => {
    const current = readForm();
    const prev = pick(selected, [
      "name",
      "subject_template",
      "body_text_template",
      "body_html_template",
    ]);
    const changed = JSON.stringify(current) !== JSON.stringify(prev);
    setDirty(changed);
  });

  setSelected(emptyTemplate());
  await loadTemplates();
}
