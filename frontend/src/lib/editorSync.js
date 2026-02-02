export function textToHtml(text) {
  const t = (text || "").trim();
  if (!t) return "";

  const lines = t.split("\n");
  const html = lines
    .map((line) => line.trim())
    .map((line) => (line ? `<p>${escapeHtml(line)}</p>` : "<p><br/></p>"))
    .join("");

  return html;
}

export function htmlToText(html) {
  const h = (html || "").trim();
  if (!h) return "";

  try {
    const doc = new DOMParser().parseFromString(h, "text/html");
    const text = (doc.body.textContent || "").replace(/\n{3,}/g, "\n\n").trim();
    return text;
  } catch {
    return "";
  }
}

function escapeHtml(s) {
  return (s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
