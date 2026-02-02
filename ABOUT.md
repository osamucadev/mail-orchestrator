# Mail Orchestrator

Local-first email composer and sent mail tracker powered by Gmail.  
Built as a portfolio-grade project with clean architecture, strong UI identity, and a future-proof backend design.

Repository name: `mail-orchestrator`  
Project name: `Mail Orchestrator`

## Product overview

A local app with two decoupled parts:

- **Frontend**: HTML, SCSS, and vanilla JavaScript running on a dev server with hot reload
- **Backend**: Python with FastAPI, REST, native Swagger, and hot reload
- **Database**: local SQLite
- **Google login**: local OAuth using an existing GCP project
- **Gmail integration**: send and read emails via Gmail API
- **History**: sent list with reply status, manual recheck, and resend
- **Templates**: placeholders detected automatically and rendered as dynamic fields

## Stack decisions

### Backend

- **FastAPI**  
  Provides Swagger at `/docs` and OpenAPI at `/openapi.json`.
- **SQLite**  
  Local file-based database, ideal for local-first and portfolio iteration.
- **SQLAlchemy + Alembic**  
  ORM plus migrations to keep the project ready for a future deployment.
- **Google Auth + Gmail API**  
  OAuth flow and Gmail API calls.

### Frontend

- **Vite** as dev server  
  The code stays vanilla, while Vite delivers hot reload and an easy build pipeline.
- **SCSS** compiled via Vite pipeline.

## One-command development workflow

At the repository root, a single command runs everything:

- backend with hot reload
- frontend with hot reload
- opens the browser automatically

Target command:

- `npm run dev`

## Gmail constraints that shape the system

### Sending emails

Gmail API can send via `messages.send` or `drafts.send` using an RFC 2822 message encoded as base64url in the `raw` field.

This supports:

- plain text
- HTML
- attachments
- inline images via MIME

### Reply detection

The system must store `threadId` and `messageId` returned when sending.

To check if an email was replied to, the app fetches the thread and verifies whether a later message exists from someone else. Gmail conversations are thread-based and support thread retrieval.

### Pasted images inside the editor

Gmail is not friendly with base64 images directly inside the HTML body.

The most compatible approach is attaching pasted images as MIME inline parts and referencing them using `cid:` in the HTML.

### Local OAuth

For a local app, the installed application flow usually uses a redirect to `http://localhost` and works well for local development.

## Database model (SQLite)

### Table: `emails`

Main fields:

- `id` (uuid or int)
- `gmail_message_id` (string)
- `gmail_thread_id` (string)
- `to` (string)
- `subject` (string)
- `body_text` (text)
- `body_html` (text)
- `sent_at` (datetime)
- `responded` (bool)
- `responded_at` (datetime, nullable)
- `responded_source` (enum: `gmail`, `manual`)
- `last_checked_at` (datetime, nullable)

### Table: `email_attachments`

- `id`
- `email_id` (fk)
- `filename`
- `mime_type`
- `size_bytes`
- `storage_path` (local storage path)
- `disposition` (enum: `attachment`, `inline`)
- `content_id` (for inline CID references)

### Table: `templates`

- `id`
- `name`
- `subject_template`
- `body_text_template`
- `body_html_template`

### Table: `template_placeholders`

- `id`
- `template_id`
- `key` (example: `{{company}}`)
- `label` (example: `Company`)
- `order_index`

This supports generating placeholder-driven forms on the frontend.

### Table: `settings`

- `id` (always 1)
- thresholds for time emojis:
  - `t_white_minutes`
  - `t_blue_minutes`
  - `t_yellow_minutes`
  - `t_red_minutes`

Emoji rules:

- replied always uses `🟢`
- otherwise select `⚪🔵🟡🔴` based on elapsed time since `sent_at`

## REST API (with Swagger)

### Auth

- `GET /api/auth/status`
- `POST /api/auth/login`  
  Starts OAuth and returns a consent URL
- `GET /api/auth/callback`  
  Receives code and stores tokens
- `POST /api/auth/logout`

### Emails

- `POST /api/emails/send`  
  Payload includes: `to`, `subject`, `body_text`, `body_html`, attachment metadata, inline image mapping
- `GET /api/emails/history?limit=50&offset=0`
- `POST /api/emails/{id}/resend`
- `POST /api/emails/{id}/check-reply`
- `POST /api/emails/{id}/mark-responded`  
  Manual override

### Templates

- `GET /api/templates`
- `POST /api/templates`
- `GET /api/templates/{id}`
- `PUT /api/templates/{id}`
- `DELETE /api/templates/{id}`
- `GET /api/templates/{id}/placeholders`  
  Returns detected placeholders

### Settings

- `GET /api/settings`
- `PUT /api/settings`

## Templates and placeholders

Placeholder format:

- `{{name}}`, `{{company}}`, `{{role}}`
- any identifier matching `a-zA-Z0-9_`

How placeholders are discovered:

- regex: `\{\{\s*([a-zA-Z0-9_]+)\s*\}\}`
- unique keys collected
- ordered by first appearance
- stored in `template_placeholders`

Composer flow:

- user selects a template
- frontend fetches `/placeholders`
- frontend renders placeholder inputs dynamically
- backend substitutes placeholder values into subject and body at send time

## Editor requirements

Two editing modes must remain synchronized:

- Text tab
- HTML tab

Practical sync approach:

- Text to HTML: convert line breaks into `<br>` and wrap into `<p>`
- HTML to Text: use `DOMParser` and extract `textContent` while preserving main breaks

Expected limitation:

Perfect bidirectional conversion is a deep problem. This project targets recruitment and follow-up workflows, where this approach is reliable and easy to explain as an intentional tradeoff.

Editor UI plan:

- 3 tabs: `Text`, `HTML`, `Preview`
- when editing Text, the HTML tab shows the generated HTML
- when editing HTML, the Text tab shows the extracted plain text
- Preview renders the final HTML output

## Attachments and pasted images

Requirements:

- attachments are managed in a separate field outside the message editor
- pasted images from clipboard are supported

Suggested behavior:

- when an image is pasted, it becomes an item in an Inline Images panel
- HTML editor inserts `<img src="cid:...">`
- text editor inserts `[image: filename.png]`

Send pipeline:

- build a MIME multipart message
  - `alternative`: `text/plain` and `text/html`
  - `related`: inline images with Content-ID
  - `mixed`: regular attachments

## History, refresh, status, resend

History entries display:

- subject
- recipient
- absolute sent date
- relative time like “X minutes ago”, “X hours ago”, “X days ago”
- emoji `⚪🔵🟡🔴` based on configurable thresholds
- `🟢` when replied, either Gmail-detected or manual

Per-item actions:

- check reply now
- mark as replied manually
- resend

Reply check:

- fetch Gmail thread and check whether there is a later message from a different sender after `sent_at`

## Follow-ups in the future

Not implemented now, but designed for it.

Future table concept: `email_followups`

- `parent_email_id`
- `subject`
- `body_text`
- `body_html`
- `order_index`

Future resend flow:

- user chooses to resend the original or a follow-up variant

For now:

- keep architecture and folder structure ready for this feature.

## Repository folder structure

```text
mail-orchestrator/
  backend/
    app/
      api/
      core/
      db/
      gmail/
      models/
      schemas/
      services/
    tests/
    pyproject.toml
    alembic.ini
  frontend/
    src/
      assets/
      styles/
      pages/
      components/
    index.html
    vite.config.js
    package.json
  scripts/
    dev.mjs
  README.md
  package.json
```