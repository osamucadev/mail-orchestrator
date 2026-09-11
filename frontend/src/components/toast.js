let container = null;

function ensureContainer() {
  if (container) return container;

  container = document.createElement("div");
  container.className = "toast-stack";
  document.body.appendChild(container);
  return container;
}

export function toast(message, variant = "muted", duration = 5000) {
  const root = ensureContainer();

  const el = document.createElement("div");
  el.className = `toast toast--${variant}`;
  el.setAttribute("role", variant === "error" ? "alert" : "status");
  el.style.setProperty("--toast-duration", `${duration}ms`);

  const text = document.createElement("span");
  text.className = "toast-message";
  text.textContent = message;

  const closeButton = document.createElement("button");
  closeButton.className = "toast-close";
  closeButton.type = "button";
  closeButton.setAttribute("aria-label", "Dismiss notification");
  closeButton.textContent = "×";

  const progress = document.createElement("span");
  progress.className = "toast-progress";
  progress.setAttribute("aria-hidden", "true");

  el.append(text, closeButton, progress);

  root.appendChild(el);

  let removed = false;
  let removalTimer;
  const dismiss = () => {
    if (removed) return;
    removed = true;
    clearTimeout(removalTimer);
    el.classList.remove("is-in");
    setTimeout(() => el.remove(), 180);
  };

  closeButton.addEventListener("click", dismiss);

  requestAnimationFrame(() => {
    el.classList.add("is-in");
  });

  removalTimer = setTimeout(dismiss, duration);
}
