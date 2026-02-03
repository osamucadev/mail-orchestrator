export async function getAuthUrl() {
  const res = await fetch("http://localhost:8000/api/auth/login", {
    method: "POST",
  });

  if (!res.ok) throw new Error("Failed to get auth URL");

  const data = await res.json();
  return data.auth_url;
}

export function openAuthPopup(authUrl) {
  const width = 500;
  const height = 600;
  const left = window.innerWidth / 2 - width / 2;
  const top = window.innerHeight / 2 - height / 2;

  const popup = window.open(
    authUrl,
    "gmail-auth",
    `width=${width},height=${height},left=${left},top=${top}`,
  );

  return new Promise((resolve, reject) => {
    if (!popup) {
      reject(new Error("Popup blocked"));
      return;
    }

    // Check every 500ms if popup closed and redirected
    const checkInterval = setInterval(() => {
      try {
        // After Google redirects to backend callback, backend redirects to frontend
        // We detect this by checking if popup was closed
        if (popup.closed) {
          clearInterval(checkInterval);
          // Give backend time to save token, then check auth status
          setTimeout(() => {
            checkAuthStatus().then(resolve).catch(reject);
          }, 500);
        }
      } catch (e) {
        // Cross-origin error, but popup might still be valid
      }
    }, 500);

    // Timeout after 2 minutes
    setTimeout(() => {
      clearInterval(checkInterval);
      popup.close();
      reject(new Error("Auth timeout"));
    }, 120000);
  });
}

export async function checkAuthStatus() {
  const res = await fetch("http://localhost:8000/api/auth/status");

  if (!res.ok) throw new Error("Failed to check auth status");

  const data = await res.json();
  return data.authenticated;
}

export async function logout() {
  const res = await fetch("http://localhost:8000/api/auth/logout", {
    method: "POST",
  });

  if (!res.ok) throw new Error("Failed to logout");

  return true;
}
