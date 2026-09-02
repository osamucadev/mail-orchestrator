# Frontend

Vanilla JavaScript, HTML and SCSS, built with Vite. Production Docker serves
`dist/` through Nginx.

## Development and build

From `frontend/`:

```sh
npm ci
npm run dev
npm run build
```

The development URL is [http://localhost:5173](http://localhost:5173). Start the
backend separately or use the root `npm run dev` workflow after
[setup](../SETUP.md). Running `npm run preview` uses Vite's preview port unless
overridden; account requests still require a matching backend frontend Origin.

`VITE_API_BASE` defaults to `http://localhost:8000`. Set it before running Vite
or building, for example in `frontend/.env.local`. It is not an Nginx runtime
variable and the Dockerfile does not currently accept a corresponding build arg.

## Account behavior

- `src/lib/oauth.js` handles browser-bound OAuth and account selection.
- The HttpOnly session cookie is sent with `credentials: "include"`.
- `src/lib/api.js` includes `X-Account-ID` on JSON and multipart requests.
- Only the selected account ID is stored in `sessionStorage`; Google credentials
  never go into frontend storage.
- `src/pages/appShell.js` lists connected accounts, shows the sender and provides
  add/reconnect/disconnect controls.
- Switching accounts requires confirmation and reloads the page. Unsaved drafts
  and form edits are discarded instead of carried into the other account.
- The callback is handled before rendering the normal application. Popup results
  are checked against the expected source/origin and server account status.
- The same-tab login link supports browsers where popups are blocked or awkward.
- Disconnecting an account retains its saved data, but removes its app connection
  in every browser.

New Gmail accounts have empty history/templates and independent settings.
Selecting a different Gmail must never be implemented as frontend filtering alone.

## Pages and editor

- `composePage.js`: visual Editor/Preview, template fields, uploads and send.
- `historyPage.js`: sort/pagination, reply checks, resend and local deletion.
- `templatesPage.js`: account-specific CRUD and detected placeholders.
- `settingsPage.js`: independent emoji thresholds.
- `router.js`: hash routes; unknown routes fall back to Compose.

The backend detects placeholder keys. The composer substitutes values in the
frontend before sending. Inline images use data URLs for browser preview and
CID references in the MIME message. Actual files are uploaded as multipart;
JSON attachment paths are not accepted by the backend.

The SVG favicon is `src/assets/favicon.svg`, referenced by `index.html` and
emitted by Vite with a fingerprinted production filename.

## Isolated browser testing

This optional fixture uses a temporary database and fake Google authorization.
It is not shipped in the production image. No real credentials are needed and
sending is disabled.

Terminal 1, from `backend/` with the test dependencies installed:

```sh
.venv/bin/python -m tests.serve_browser_fixture
```

Terminal 2, from `frontend/`, on Linux/macOS:

```sh
VITE_API_BASE=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

On PowerShell, set `$env:VITE_API_BASE = "http://127.0.0.1:8001"` before the same
npm command; use the Windows virtual-environment Python path in terminal 1.

Open [the test frontend](http://127.0.0.1:5174) and connect `first@example.com`.
Create a template, add `second@example.com`, and confirm the second account is
empty. Switch back and confirm the first template remains. Also test cancellation,
same-tab login, refresh and disconnect/reconnect. Stop both test servers afterward.

Use 127.0.0.1 for the fixture, not the production app's localhost origin.
The backend unit/integration suite is documented in [backend/README.md](../backend/README.md).
