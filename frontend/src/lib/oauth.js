const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const ACTIVE_ACCOUNT_KEY = "mail-orchestrator.active-account";
let activeAccountId = sessionStorage.getItem(ACTIVE_ACCOUNT_KEY);

export function getActiveAccountId() {
  return activeAccountId;
}

export function selectAccount(id) {
  activeAccountId = id == null ? null : String(id);
  if (activeAccountId) sessionStorage.setItem(ACTIVE_ACCOUNT_KEY, activeAccountId);
  else sessionStorage.removeItem(ACTIVE_ACCOUNT_KEY);
}

export async function getAuthStatus() {
  const res = await fetch(`${API_BASE}/api/auth/status`, { credentials: "include", cache: "no-store" });
  if (!res.ok) throw new Error("Failed to check connected accounts. Try reloading.");
  return res.json();
}

export async function checkAuthStatus() {
  const data = await getAuthStatus();
  if (!data.accounts.some((account) => String(account.id) === activeAccountId)) {
    selectAccount(data.accounts[0]?.id ?? null);
  }
  return data.authenticated;
}

export async function getAuthUrl() {
  const res = await fetch(`${API_BASE}/api/auth/login`, { method: "POST", credentials: "include" });
  if (!res.ok) throw new Error("Failed to start Gmail login");
  return (await res.json()).auth_url;
}

export function openAuthPopup(authUrl, existingPopup) {
  const popup = existingPopup || window.open(authUrl, "gmail-auth", "width=520,height=680");
  if (!popup) return Promise.reject(new Error("Popup blocked. Allow popups and try again."));
  return new Promise((resolve, reject) => {
    let finished = false;
    const finish = (error, account) => {
      if (finished) return;
      finished = true;
      clearInterval(interval);
      clearTimeout(timeout);
      window.removeEventListener("message", onMessage);
      popup.close();
      if (error) reject(error);
      else resolve(account);
    };
    const onMessage = async (event) => {
      if (event.origin !== window.location.origin || event.source !== popup || event.data?.type !== "gmail-auth-result") return;
      if (event.data.error) {
        finish(new Error("Gmail authorization failed or was cancelled. Try again."));
        return;
      }
      try {
        const data = await getAuthStatus();
        const account = data.accounts.find((item) => String(item.id) === String(event.data.accountId));
        if (!account) throw new Error("Account was not connected. Try again.");
        selectAccount(account.id);
        finish(null, account);
      } catch (error) {
        finish(error);
      }
    };
    window.addEventListener("message", onMessage);
    const interval = setInterval(() => {
      if (popup.closed) finish(new Error("Gmail login window was closed before completion."));
    }, 500);
    const timeout = setTimeout(() => finish(new Error("Gmail login timed out. Try again.")), 600000);
    if (existingPopup) popup.location.href = authUrl;
  });
}

export async function connectAccount(onAuthUrl = () => {}) {
  // Open during the click gesture so slow requests do not trigger popup blockers.
  const popup = window.open("about:blank", "gmail-auth", "width=520,height=680");
  const closePopup = () => popup?.close();
  window.addEventListener("pagehide", closePopup, { once: true });
  try {
    const url = await getAuthUrl();
    onAuthUrl(url);
    if (!popup) throw new Error("Popup blocked. Use the link to continue in this tab.");
    return await openAuthPopup(url, popup);
  } catch (error) {
    popup?.close();
    throw error;
  } finally {
    window.removeEventListener("pagehide", closePopup);
  }
}

export async function logout() {
  const res = await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST", credentials: "include", headers: { "X-Account-ID": activeAccountId || "" },
  });
  if (!res.ok) throw new Error("Failed to disconnect account");
  selectAccount(null);
}
