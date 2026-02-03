export function renderAuthCallback() {
  document.body.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif;">
      <div style="text-align: center;">
        <p>Authenticating...</p>
        <p style="font-size: 12px; color: #999;">This window will close automatically.</p>
      </div>
    </div>
  `;

  // Close popup after a short delay
  setTimeout(() => {
    window.close();
  }, 500);
}
