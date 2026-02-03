import { getAuthUrl, openAuthPopup, checkAuthStatus } from "../lib/oauth";
import { toast } from "./toast";

export function renderLoginModal(root) {
  root.innerHTML = `
    <div class="modal modal--auth">
      <div class="modal-backdrop"></div>
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h2 class="modal-title">Login with Gmail</h2>
          </div>
          
          <div class="modal-body">
            <p>You need to authenticate with Gmail to use Mail Orchestrator.</p>
            <p class="hint">A popup window will open for you to authorize access.</p>
          </div>
          
          <div class="modal-footer">
            <button class="btn btn--primary" data-action="login">Open Gmail Login</button>
          </div>
          
          <div class="modal-status" data-role="status"></div>
        </div>
      </div>
    </div>
  `;

  const statusEl = root.querySelector('[data-role="status"]');
  const loginBtn = root.querySelector('[data-action="login"]');

  function setStatus(text, kind = "muted") {
    statusEl.textContent = text;
    statusEl.className = `modal-status status status--${kind}`;
  }

  loginBtn.addEventListener("click", async () => {
    loginBtn.disabled = true;
    setStatus("Opening Gmail login...", "muted");

    try {
      const authUrl = await getAuthUrl();
      setStatus("Authorize in the popup window...", "muted");

      await openAuthPopup(authUrl);

      setStatus("Successfully logged in!", "ok");
      toast("Logged in successfully", "ok");

      // Close modal and reload app
      setTimeout(() => {
        root.innerHTML = "";
        window.location.reload();
      }, 1000);
    } catch (err) {
      setStatus(err.message, "error");
      toast("Login failed: " + err.message, "error");
      loginBtn.disabled = false;
    }
  });
}
