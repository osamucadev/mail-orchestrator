import "./styles/main.scss"
import { renderAppShell } from "./pages/appShell"
import { renderAuthCallback } from "./pages/authCallback"

if (window.location.hash.startsWith("#auth-callback")) {
  renderAuthCallback()
} else {
  renderAppShell(document.querySelector("#app"))
}
