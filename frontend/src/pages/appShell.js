import { renderLoginModal } from "../components/loginModal";
import { connectAccount, getActiveAccountId, getAuthStatus, logout, selectAccount } from "../lib/oauth";
import { getRoute, renderRoute } from "./router";

function confirmAccountAction(message) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "account-confirmation";
    dialog.innerHTML = '<form method="dialog"><p></p><button class="btn" value="cancel" autofocus>Cancel</button> <button class="btn btn--primary" value="continue">Continue</button></form>';
    dialog.querySelector("p").textContent = message;
    dialog.addEventListener("close", () => {
      resolve(dialog.returnValue === "continue");
      dialog.remove();
    }, { once: true });
    document.body.append(dialog);
    dialog.showModal();
  });
}

function setActiveNav(root) {
  const route = getRoute();
  for (const link of root.querySelectorAll(".nav-link")) {
    link.classList.toggle("is-active", link.getAttribute("href").replace("#", "") === route);
  }
}

export async function renderAppShell(root) {
  let status;
  try {
    status = await getAuthStatus();
  } catch (error) {
    root.textContent = error.message;
    return;
  }
  if (!status.authenticated) {
    selectAccount(null);
    renderLoginModal(root);
    return;
  }
  const active = status.accounts.find((account) => String(account.id) === getActiveAccountId()) || status.accounts[0];
  selectAccount(active.id);
  root.innerHTML = `
    <header class="topbar">
      <div class="container topbar-inner">
        <div class="brand">
          <span class="brand-mark">MO</span>
          <span class="brand-name">Mail Orchestrator</span>
        </div>
        <nav class="nav">
          <a class="nav-link" href="#compose">Compose</a>
          <a class="nav-link" href="#history">History</a>
          <a class="nav-link" href="#templates">Templates</a>
          <a class="nav-link" href="#settings">Settings</a>
        </nav>
      </div>
      <div class="container account-toolbar">
        <label for="active-account">Gmail / sender</label>
        <select id="active-account" aria-label="Active Gmail account"></select>
        <button class="btn" data-action="add-account">Add / reconnect account</button>
        <button class="btn" data-action="disconnect-account">Disconnect account</button>
        <span class="hint">History, templates and settings are private to this account.</span>
        <span class="account-status" role="status" aria-live="polite"></span>
        <a data-role="login-fallback" hidden>Continue login in this tab</a>
      </div>
    </header>
    <main class="page" data-role="page"></main>
  `;
  const selector = root.querySelector("#active-account");
  for (const account of status.accounts) {
    selector.add(new Option(account.email, String(account.id), false, account.id === active.id));
  }
  const feedback = root.querySelector(".account-status");
  selector.addEventListener("change", async () => {
    if (!await confirmAccountAction("Switch Gmail account? Unsaved changes on this page will be discarded.")) {
      selector.value = String(active.id);
      return;
    }
    selectAccount(selector.value);
    window.location.reload();
  });
  const add = root.querySelector('[data-action="add-account"]');
  const disconnect = root.querySelector('[data-action="disconnect-account"]');
  add.addEventListener("click", async () => {
    if (!await confirmAccountAction("Connect a Gmail account? After login the page will reload; unsaved changes will be discarded.")) return;
    add.disabled = disconnect.disabled = selector.disabled = true;
    feedback.textContent = "Complete authorization in the Gmail window...";
    try {
      await connectAccount((url) => {
        const fallback = root.querySelector('[data-role="login-fallback"]');
        fallback.href = url;
        fallback.hidden = false;
      });
      window.location.reload();
    } catch (error) {
      feedback.textContent = error.message;
      add.disabled = disconnect.disabled = selector.disabled = false;
    }
  });
  disconnect.addEventListener("click", async () => {
    if (!await confirmAccountAction(`Disconnect ${active.email} from this app on all browsers? Saved data is kept; unsaved edits will be discarded.`)) return;
    add.disabled = disconnect.disabled = selector.disabled = true;
    try {
      await logout();
      window.location.reload();
    } catch (error) {
      feedback.textContent = error.message;
      add.disabled = disconnect.disabled = selector.disabled = false;
    }
  });
  const page = root.querySelector('[data-role="page"]');
  function run() {
    setActiveNav(root);
    renderRoute(page);
  }
  window.addEventListener("hashchange", run);
  run();
}
