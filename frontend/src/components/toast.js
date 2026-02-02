let container = null;
let timer = null;

function ensureContainer() {
  if (container) return container;

  container = document.createElement("div");
  container.className = "toast-stack";
  document.body.appendChild(container);
  return container;
}

export function toast(message, variant = "muted") {
  const root = ensureContainer();

  const el = document.createElement("div");
  el.className = `toast toast--${variant}`;
  el.textContent = message;

  root.appendChild(el);

  requestAnimationFrame(() => {
    el.classList.add("is-in");
  });

  clearTimeout(timer);
  timer = setTimeout(() => {
    el.classList.remove("is-in");
    setTimeout(() => el.remove(), 180);
  }, 2200);
}
