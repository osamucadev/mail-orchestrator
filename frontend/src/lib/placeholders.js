const PLACEHOLDER_RE = /\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g;

export function extractPlaceholders(text) {
  const found = new Set();
  const order = [];
  let m;

  while ((m = PLACEHOLDER_RE.exec(text || "")) !== null) {
    const key = m[1];
    if (!found.has(key)) {
      found.add(key);
      order.push(key);
    }
  }

  return order;
}

export function applyPlaceholders(text, values) {
  return (text || "").replace(PLACEHOLDER_RE, (_, key) => {
    const v = values?.[key];
    return v === undefined || v === null ? `{{${key}}}` : String(v);
  });
}
