import { selectAccount } from "../lib/oauth";

export function renderAuthCallback() {
  const returnToApp = () => {
    window.history.replaceState(null, "", "/#compose");
    window.location.reload();
  };
  const params = new URLSearchParams(window.location.hash.split("?")[1] || "");
  const error = params.get("error");
  const accountId = params.get("account_id");
  document.body.textContent = error
    ? "Gmail authorization failed or was cancelled. Return to the main window and try again."
    : "Account connected. You may return to the main window.";
  if (window.opener) {
    window.opener.postMessage({ type: "gmail-auth-result", accountId, error }, window.location.origin);
  } else if (!error && accountId) {
    selectAccount(accountId);
    returnToApp();
  } else {
    const back = document.createElement("a");
    back.href = "/#compose";
    back.textContent = " Return to login";
    back.addEventListener("click", (event) => {
      event.preventDefault();
      returnToApp();
    });
    document.body.append(back);
  }
}
