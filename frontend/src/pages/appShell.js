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
        <div class="topbar-actions">
          <nav class="nav" aria-label="Main navigation">
            <a class="nav-link" href="#compose">Compose</a>
            <a class="nav-link" href="#history">History</a>
            <a class="nav-link" href="#templates">Templates</a>
            <a class="nav-link" href="#settings">Settings</a>
          </nav>

          <details class="account-menu" data-role="account-menu">
            <summary aria-label="Open sender account menu">
              <span class="account-avatar" aria-hidden="true">@</span>
              <span class="account-summary">
                <span class="account-summary-label">From</span>
                <span class="account-summary-email" data-role="active-account-email"></span>
              </span>
              <span class="account-chevron" aria-hidden="true"></span>
            </summary>

            <div class="account-popover">
              <div class="account-popover-head">
                <span class="account-popover-eyebrow">Sender account</span>
                <strong>Choose who sends this email</strong>
              </div>

              <label class="account-select-label" for="active-account">Gmail account</label>
              <select id="active-account" aria-label="Active Gmail account"></select>

              <div class="account-menu-actions">
                <button class="btn" data-action="add-account">Reconnect or add</button>
                <button class="btn btn--ghost account-disconnect" data-action="disconnect-account">Disconnect</button>
              </div>

              <span class="account-status" role="status" aria-live="polite"></span>
              <a class="account-login-fallback" data-role="login-fallback" hidden>Continue login in this tab</a>
              <p class="account-privacy">History, templates and settings stay separate for each account.</p>
            </div>
          </details>
        </div>
      </div>
    </header>
    <main class="page" data-role="page"></main>
  `;
  const selector = root.querySelector("#active-account");
  for (const account of status.accounts) {
    selector.add(new Option(account.email, String(account.id), false, account.id === active.id));
  }
  root.querySelector('[data-role="active-account-email"]').textContent = active.email;
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
    if (!await confirmAccountAction("Connect a Gmail account? Reconnecting the current account will keep this draft. Choosing a different account will reload the page and discard unsaved changes.")) return;
    add.disabled = disconnect.disabled = selector.disabled = true;
    feedback.textContent = "Complete authorization in the Gmail window...";
    try {
      const connectedAccount = await connectAccount((url) => {
        const fallback = root.querySelector('[data-role="login-fallback"]');
        fallback.href = url;
        fallback.hidden = false;
      });

      // A token refresh failure only requires replacing this account's Google
      // credentials. Keep the current DOM alive so an in-progress message,
      // including File objects selected as attachments, is not discarded.
      if (String(connectedAccount.id) === String(active.id)) {
        selector.value = String(connectedAccount.id);
        feedback.textContent = `${connectedAccount.email} reconnected. Your draft was kept.`;
        root.querySelector('[data-role="login-fallback"]').hidden = true;
        add.disabled = disconnect.disabled = selector.disabled = false;
        return;
      }

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
  let page = root.querySelector('[data-role="page"]');
  function run() {
    setActiveNav(root);

    // Each page registers event handlers on its root. Replace that root during
    // navigation so handlers from earlier visits cannot fire a second send or
    // resend with stale form/history state.
    const freshPage = page.cloneNode(false);
    page.replaceWith(freshPage);
    page = freshPage;
    renderRoute(page);
  }
  window.addEventListener("hashchange", run);
  run();
}
