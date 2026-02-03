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

function uid(prefix = "id") {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`;
}

function formatBytes(bytes) {
  const b = Number(bytes || 0);
  if (b < 1024) return `${b} B`;
  const kb = b / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}

function dataUrlToBlob(dataUrl) {
  const [meta, base64] = dataUrl.split(",");
  const mime =
    meta.match(/data:(.*);base64/)?.[1] || "application/octet-stream";

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  return new Blob([bytes], { type: mime });
}

export function renderComposePage(root) {
  root.innerHTML = `
    <section class="page-shell">
      <div class="container">
        <div class="page-head">
          <div>
            <h2 class="page-title">Compose</h2>
            <p class="page-subtitle">
              Write in HTML. Paste images from clipboard. Attach files outside the editor.
            </p>
          </div>

          <div class="page-actions">
            <button class="btn btn--ghost" data-action="reset">Reset</button>
            <button class="btn" data-action="send">Send</button>
          </div>
        </div>

        <div class="grid grid--compose">
          <section class="panel panel--main">
            <div class="panel-head">
              <h3 class="panel-title">Message</h3>
              <div class="panel-actions">
                <span class="status status--muted" data-role="status"></span>
              </div>
            </div>

            <form class="form" data-role="form">
              <div class="cols cols--2">
                <label class="field">
                  <span class="label">To</span>
                  <input class="input" name="to" placeholder="someone@example.com" autocomplete="off" />
                </label>

                <label class="field">
                  <span class="label">Subject</span>
                  <input class="input" name="subject" placeholder="Quick follow up" autocomplete="off" />
                </label>
              </div>

            <div class="panel panel--inner">
            <div class="panel-head">
                <h3 class="panel-title">Template</h3>
                <div class="panel-actions">
                <button class="btn btn--ghost" type="button" data-action="templates-refresh">Refresh</button>
                </div>
            </div>

            <div class="cols cols--2">
                <label class="field">
                <span class="label">Select template</span>
                <select class="select" name="template_id" data-role="template-select">
                    <option value="">No template</option>
                </select>
                <span class="hint">Selecting a template will generate placeholder inputs.</span>
                </label>

                <div class="field">
                <span class="label">Mode</span>
                <div class="mode-row">
                    <span class="badge" data-role="template-mode">Manual</span>
                    <button class="btn btn--ghost" type="button" data-action="template-clear" disabled>Clear template</button>
                </div>
                <span class="hint">Manual means no substitution is applied.</span>
                </div>
            </div>

            <div class="placeholders" data-role="placeholders">
                <div class="empty">Select a template to see placeholders.</div>
            </div>
            </div>

              <div class="tabs" role="tablist">
                <button class="tab is-active" type="button" data-tab="html" role="tab">Editor</button>
                <button class="tab" type="button" data-tab="preview" role="tab">Preview</button>
              </div>

              <div class="editor">
                <div class="editor-pane is-active" data-pane="html">
                  <textarea class="textarea" name="body_html" rows="14" placeholder="Write your message here. Press Enter for line break, Ctrl+Enter for visual line break."></textarea>
                </div>

                <div class="editor-pane" data-pane="preview">
                  <div class="preview" data-role="preview"></div>
                </div>
              </div>

              <div class="panel panel--inner">
                <div class="panel-head">
                  <h3 class="panel-title">Inline images</h3>
                  <div class="panel-actions">
                    <span class="badge" data-role="inline-count">0</span>
                  </div>
                </div>

                <div class="inline-grid" data-role="inline-list">
                  <div class="empty">Paste an image into the editor to add inline images.</div>
                </div>

                <p class="hint">
                  Tip: click inside the editor and paste an image. It will be referenced in HTML using <code>cid:</code>.
                </p>
              </div>
            </form>
          </section>

          <aside class="panel">
            <div class="panel-head">
              <h3 class="panel-title">Attachments</h3>
              <div class="panel-actions">
                <label class="btn btn--ghost" style="cursor:pointer;">
                  Add
                  <input type="file" multiple data-role="file-input" style="display:none;" />
                </label>
              </div>
            </div>

            <div class="attachments" data-role="attachments">
              <div class="empty">No attachments.</div>
            </div>

            <div class="panel panel--inner">
              <div class="panel-head">
                <h3 class="panel-title">Notes</h3>
              </div>
              <ul class="bullets">
                <li>Attachments are outside the message editor.</li>
                <li>Inline images are attached with disposition <code>inline</code>.</li>
                <li>Press <code>Enter</code> for &lt;br /&gt;, <code>Ctrl+Enter</code> for visual line break.</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </section>
  `;

  const els = {
    status: root.querySelector('[data-role="status"]'),
    form: root.querySelector('[data-role="form"]'),
    preview: root.querySelector('[data-role="preview"]'),
    tabs: Array.from(root.querySelectorAll(".tab")),
    panes: Array.from(root.querySelectorAll("[data-pane]")),
    fileInput: root.querySelector('[data-role="file-input"]'),
    attachments: root.querySelector('[data-role="attachments"]'),
    inlineList: root.querySelector('[data-role="inline-list"]'),
    inlineCount: root.querySelector('[data-role="inline-count"]'),
    btnSend: root.querySelector('[data-action="send"]'),
    btnReset: root.querySelector('[data-action="reset"]'),
    templateSelect: root.querySelector('[data-role="template-select"]'),
    templateMode: root.querySelector('[data-role="template-mode"]'),
    placeholders: root.querySelector('[data-role="placeholders"]'),
    btnTemplatesRefresh: root.querySelector(
      '[data-action="templates-refresh"]',
    ),
    btnTemplateClear: root.querySelector('[data-action="template-clear"]'),
  };

  let activeTab = "html";

  const state = {
    attachments: [],
    inlineImages: [],
  };

  const templateState = {
    active: false,
    templateId: null,
    placeholders: [],
    values: {},
    raw: {
      subject: "",
      html: "",
    },
  };

  let templatesCache = [];

  function setStatus(text, kind = "muted") {
    els.status.textContent = text || "";
    els.status.className = `status status--${kind}`;
  }

  function setActiveTab(tab) {
    activeTab = tab;
    for (const t of els.tabs)
      t.classList.toggle("is-active", t.getAttribute("data-tab") === tab);
    for (const p of els.panes)
      p.classList.toggle("is-active", p.getAttribute("data-pane") === tab);

    if (tab === "preview") renderPreview();
  }

  function renderPreview() {
    let html = els.form.body_html.value || "";

    for (const img of state.inlineImages) {
      html = html.replaceAll(`cid:${img.content_id}`, img.dataUrl);
    }

    els.preview.innerHTML =
      html || `<div class="empty">Nothing to preview yet.</div>`;
  }

  function renderAttachments() {
    if (!state.attachments.length) {
      els.attachments.innerHTML = `<div class="empty">No attachments.</div>`;
      return;
    }

    els.attachments.innerHTML = state.attachments
      .map((a, idx) => {
        return `
          <div class="file-row">
            <div class="file-main">
              <div class="file-name">${escapeHtml(a.filename)}</div>
              <div class="file-sub mono">${escapeHtml(a.mime_type)} · ${formatBytes(a.size_bytes)}</div>
            </div>
            <button class="btn btn--ghost" type="button" data-action="remove-attachment" data-index="${idx}">Remove</button>
          </div>
        `;
      })
      .join("");
  }

  function renderInlineImages() {
    els.inlineCount.textContent = String(state.inlineImages.length);

    if (!state.inlineImages.length) {
      els.inlineList.innerHTML = `<div class="empty">Paste an image into the editor to add inline images.</div>`;
      return;
    }

    els.inlineList.innerHTML = state.inlineImages
      .map((img, idx) => {
        return `
          <div class="inline-item">
            <div class="inline-thumb">
              <img src="${img.dataUrl}" alt="${escapeHtml(img.filename)}" />
            </div>
            <div class="inline-meta">
              <div class="file-name">${escapeHtml(img.filename)}</div>
              <div class="file-sub mono">${escapeHtml(img.mime_type)} · ${formatBytes(img.size_bytes)}</div>
              <div class="file-sub mono">cid:${escapeHtml(img.content_id)}</div>
            </div>
            <button class="btn btn--ghost" type="button" data-action="remove-inline" data-index="${idx}">Remove</button>
          </div>
        `;
      })
      .join("");
  }

  function insertInlineReference(img) {
    const html = els.form.body_html.value || "";
    const snippet = `<p><img src="cid:${img.content_id}" alt="${escapeHtml(img.filename)}"/></p>`;
    els.form.body_html.value = html ? `${html}\n${snippet}` : snippet;
    renderPreview();
  }

  async function handlePaste(e) {
    const items = e.clipboardData?.items || [];
    const imageItems = Array.from(items).filter(
      (it) => it.type && it.type.startsWith("image/"),
    );
    if (!imageItems.length) return;

    e.preventDefault();

    for (const it of imageItems) {
      const file = it.getAsFile();
      if (!file) continue;

      const id = uid("img");
      const contentId = uid("cid");
      const filename =
        file.name && file.name !== "image.png" ? file.name : `${id}.png`;

      const dataUrl = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.readAsDataURL(file);
      });

      const img = {
        id,
        filename,
        mime_type: file.type || "image/png",
        size_bytes: file.size || 0,
        dataUrl,
        content_id: contentId,
      };

      state.inlineImages.push(img);
      insertInlineReference(img);
    }

    renderInlineImages();
    setStatus("Inline image added", "ok");
  }

  function setTemplateMode(active) {
    templateState.active = active;
    els.templateMode.textContent = active ? "Template" : "Manual";
    els.btnTemplateClear.disabled = !active;
  }

  function renderTemplateOptions() {
    const options = templatesCache
      .map((t) => `<option value="${t.id}">${escapeHtml(t.name)}</option>`)
      .join("");

    const selected = templateState.templateId
      ? String(templateState.templateId)
      : "";
    els.templateSelect.innerHTML = `
      <option value="">No template</option>
      ${options}
    `;
    els.templateSelect.value = selected;
  }

  async function loadTemplates() {
    setStatus("Loading templates…", "muted");
    try {
      templatesCache = await api.templates.list();
      renderTemplateOptions();
      setStatus("Ready", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  function renderPlaceholderFields() {
    if (!templateState.active || !templateState.placeholders.length) {
      els.placeholders.innerHTML = `<div class="empty">Select a template to see placeholders.</div>`;
      return;
    }

    els.placeholders.innerHTML = `
      <div class="placeholders-grid">
        ${templateState.placeholders
          .map((p) => {
            const key = p.key;
            const label = p.label || key;
            const value = templateState.values[key] || "";
            return `
              <label class="field">
                <span class="label">${escapeHtml(label)}</span>
                <input class="input" data-ph="${escapeHtml(key)}" value="${escapeHtml(value)}" placeholder="{{${escapeHtml(key)}}}" />
                <span class="hint mono">{{${escapeHtml(key)}}}</span>
              </label>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function applyPlaceholdersToTemplate() {
    if (!templateState.active) return;

    const subject = templateState.raw.subject;
    const html = templateState.raw.html;

    // Simple placeholder substitution: {{key}} -> value
    let appliedSubject = subject;
    let appliedHtml = html;

    for (const [key, value] of Object.entries(templateState.values)) {
      const placeholder = `{{${key}}}`;
      appliedSubject = appliedSubject.replaceAll(placeholder, value);
      appliedHtml = appliedHtml.replaceAll(placeholder, value);
    }

    els.form.subject.value = appliedSubject;
    els.form.body_html.value = appliedHtml;

    if (activeTab === "preview") renderPreview();
  }

  async function activateTemplate(templateId) {
    if (!templateId) {
      clearTemplate();
      return;
    }

    setStatus("Loading template…", "muted");
    try {
      const t = await api.templates.get(templateId);
      const placeholders = await api.templates.placeholders(templateId);

      templateState.templateId = t.id;
      templateState.placeholders = placeholders || [];
      templateState.values = {};

      templateState.raw.subject = t.subject_template || "";
      templateState.raw.html = t.body_html_template || "";

      setTemplateMode(true);
      renderPlaceholderFields();
      applyPlaceholdersToTemplate();
      setStatus("Ready", "ok");
    } catch (err) {
      setStatus(err.message, "error");
    }
  }

  function clearTemplate() {
    templateState.active = false;
    templateState.templateId = null;
    templateState.placeholders = [];
    templateState.values = {};
    templateState.raw = { subject: "", html: "" };

    els.templateSelect.value = "";
    renderPlaceholderFields();
    setTemplateMode(false);
  }

  async function send() {
    const to = els.form.to.value.trim();
    const subject = els.form.subject.value.trim();
    const body_html = els.form.body_html.value || null;

    if (!to) {
      setStatus("To is required.", "error");
      return;
    }
    if (!subject) {
      setStatus("Subject is required.", "error");
      return;
    }

    // Check for attachment mention without actual attachments
    const bodyToCheck = body_html || "";
    const hasAttachmentMention =
      /attach|anexo|arquivo|file|anexa|envio|enclosed/i.test(bodyToCheck);
    const hasAttachments =
      state.attachments.length > 0 || state.inlineImages.length > 0;

    if (hasAttachmentMention && !hasAttachments) {
      const proceed = confirm(
        "Your message mentions an attachment but none is attached.\n\nSend anyway?",
      );
      if (!proceed) {
        setStatus("Send cancelled", "muted");
        return;
      }
    }

    els.btnSend.disabled = true;
    setStatus("Sending…", "muted");

    try {
      const form = new FormData();
      form.append("to", to);
      form.append("subject", subject);
      form.append("body_text", "");
      form.append("body_html", body_html || "");

      const inlineMeta = state.inlineImages.map((img) => ({
        filename: img.filename,
        content_id: img.content_id,
        mime_type: img.mime_type,
      }));

      form.append("inline_meta", JSON.stringify(inlineMeta));

      for (const img of state.inlineImages) {
        const blob = dataUrlToBlob(img.dataUrl);
        form.append("inline_images", blob, img.filename);
      }

      for (const a of state.attachments) {
        if (a.file) form.append("attachments", a.file, a.filename);
      }

      await api.emails.sendMultipart(form);

      setStatus("Saved to local history", "ok");
      window.location.hash = "#history";
    } catch (err) {
      setStatus(err.message, "error");
    } finally {
      els.btnSend.disabled = false;
    }
  }

  function reset() {
    clearTemplate();
    els.form.to.value = "";
    els.form.subject.value = "";
    els.form.body_html.value = "";
    state.attachments = [];
    state.inlineImages = [];
    renderAttachments();
    renderInlineImages();
    renderPreview();
    setStatus("Reset", "muted");
    setActiveTab("html");
  }

  // Handle Enter key in textarea
  els.form.body_html.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      if (e.ctrlKey) {
        // Ctrl+Enter: insert newline only (visual break, no <br />)
        e.preventDefault();
        const textarea = e.target;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const before = textarea.value.substring(0, start);
        const after = textarea.value.substring(end);
        textarea.value = before + "\n" + after;
        textarea.selectionStart = textarea.selectionEnd = start + 1;
      } else {
        // Enter: insert <br />
        e.preventDefault();
        const textarea = e.target;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const before = textarea.value.substring(0, start);
        const after = textarea.value.substring(end);
        textarea.value = before + "<br />" + after;
        textarea.selectionStart = textarea.selectionEnd = start + 6;
      }
      if (activeTab === "preview") renderPreview();
    }
  });

  els.tabs.forEach((t) => {
    t.addEventListener("click", () => setActiveTab(t.getAttribute("data-tab")));
  });

  els.form.body_html.addEventListener("paste", handlePaste);

  els.fileInput.addEventListener("change", (e) => {
    const files = Array.from(e.target.files || []);

    for (const f of files) {
      state.attachments.push({
        id: uid("att"),
        file: f,
        filename: f.name,
        mime_type: f.type || "application/octet-stream",
        size_bytes: f.size || 0,
      });
    }

    renderAttachments();
    setStatus("Attachment added", "ok");
    e.target.value = "";
  });

  root.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.getAttribute("data-action");
    if (action === "send") {
      send();
      return;
    }
    if (action === "reset") {
      reset();
      return;
    }

    if (action === "remove-attachment") {
      const idx = Number(btn.getAttribute("data-index"));
      if (!Number.isNaN(idx)) state.attachments.splice(idx, 1);
      renderAttachments();
      return;
    }

    if (action === "remove-inline") {
      const idx = Number(btn.getAttribute("data-index"));
      if (!Number.isNaN(idx)) state.inlineImages.splice(idx, 1);
      renderInlineImages();
      return;
    }
  });

  els.btnTemplatesRefresh.addEventListener("click", () => loadTemplates());

  els.templateSelect.addEventListener("change", (e) => {
    const id = e.target.value ? Number(e.target.value) : null;
    activateTemplate(id);
  });

  els.btnTemplateClear.addEventListener("click", () => {
    clearTemplate();
    setStatus("Template cleared", "muted");
  });

  els.placeholders.addEventListener("input", (e) => {
    const input = e.target.closest("input[data-ph]");
    if (!input) return;

    const key = input.getAttribute("data-ph");
    templateState.values[key] = input.value;
    applyPlaceholdersToTemplate();
  });

  loadTemplates();
  setStatus("Ready", "ok");
  setActiveTab("html");
  renderAttachments();
  renderInlineImages();
  renderPreview();
}
