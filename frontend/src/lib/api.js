const API_BASE = "http://localhost:8000";

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const data = await res.json();
      detail = data?.detail || JSON.stringify(data);
    } catch {
      detail = await res.text();
    }
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  templates: {
    list: () => request("/api/templates"),
    create: (payload) =>
      request("/api/templates", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    get: (id) => request(`/api/templates/${id}`),
    update: (id, payload) =>
      request(`/api/templates/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    remove: (id) => request(`/api/templates/${id}`, { method: "DELETE" }),
    placeholders: (id) => request(`/api/templates/${id}/placeholders`),
  },
  emails: {
    history: (limit = 50, offset = 0) =>
      request(`/api/emails/history?limit=${limit}&offset=${offset}`),
    send: (payload) =>
      request("/api/emails/send", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    markResponded: (id, responded = true) =>
      request(`/api/emails/${id}/mark-responded`, {
        method: "POST",
        body: JSON.stringify({ responded }),
      }),
    resend: (id) => request(`/api/emails/${id}/resend`, { method: "POST" }),
  },
  settings: {
    get: () => request("/api/settings"),
    update: (payload) =>
      request("/api/settings", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
  },
};
