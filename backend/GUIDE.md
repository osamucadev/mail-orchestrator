# Mail Orchestrator Backend - Developer Guide

## Overview

Mail Orchestrator backend is a **REST API** built with FastAPI that manages email composition, sending via Gmail API, and tracking email history with reply detection. The system uses SQLite for local storage and SQLAlchemy ORM for database management.

**Key Technologies:**
- FastAPI (Web framework)
- SQLAlchemy (ORM)
- Alembic (Database migrations)
- Gmail API (Email sending & thread tracking)
- Pydantic (Data validation)

---

## Project Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── emails.py           # Email routes (send, resend, history, etc)
│   │   └── auth.py             # OAuth authentication routes
│   │   └── templates.py        # Template CRUD routes
│   │   └── settings.py         # Settings routes
│   ├── models/
│   │   ├── email.py            # SQLAlchemy Email model
│   │   ├── email_attachment.py # Attachment model
│   │   ├── template.py         # Template model
│   │   └── settings.py         # Settings model
│   ├── schemas/
│   │   ├── email.py            # Pydantic request/response schemas
│   │   ├── template.py         # Template schemas
│   │   └── settings.py         # Settings schemas
│   ├── services/
│   │   └── email_service.py    # Business logic (create, send, resend, check replies)
│   │   └── template_service.py # Template logic
│   │   └── settings_service.py # Settings logic
│   ├── gmail/
│   │   ├── gmail_client.py     # Gmail API authentication
│   │   ├── gmail_sender.py     # Email sending (MIME building)
│   │   └── reply_detector.py   # Reply detection logic
│   ├── db/
│   │   ├── database.py         # Database connection & session
│   │   ├── base.py             # SQLAlchemy base classes
│   │   └── deps.py             # Dependency injection (get_db)
│   ├── core/
│   │   ├── config.py           # Environment configuration
│   │   └── time_utils.py       # Time formatting utilities
│   └── migrations/             # Database schema versions
├── tests/                       # Unit & integration tests
├── alembic.ini                 # Migration configuration
├── pyproject.toml              # Python dependencies
└── requirements.txt            # Pip requirements
```

---

## File-by-File Explanation

### Core Application Files

#### **`app/main.py`** - Application Entry Point
**Purpose:** Initialize FastAPI app, configure middleware, include routers.

**Key Concepts to Study:**
- FastAPI initialization
- CORS (Cross-Origin Resource Sharing)
- Route inclusion (routers)
- Middleware configuration

**What Happens:**
1. Creates FastAPI instance
2. Sets up CORS for frontend (localhost:5173)
3. Includes all API routers
4. Defines health check endpoint
```python
# Example structure
app = FastAPI()
app.add_middleware(CORSMiddleware, ...)
app.include_router(emails.router)
app.include_router(auth.router)
```

---

### API Layer (`app/api/`)

These files handle HTTP requests and responses. They act as the "controller" layer.

#### **`app/api/emails.py`** - Email Endpoints
**Purpose:** HTTP routes for email operations.

**Endpoints:**
- `POST /api/emails/send` - Send new email
- `POST /api/emails/send-multipart` - Send with file uploads
- `GET /api/emails/history` - Fetch email history
- `POST /api/emails/{id}/resend` - Resend existing email
- `POST /api/emails/{id}/check-reply` - Check for replies
- `POST /api/emails/{id}/mark-responded` - Mark as replied
- `DELETE /api/emails/{id}` - Delete email

**Key Concepts to Study:**
- HTTP status codes (201 Created, 404 Not Found, etc)
- FastAPI dependency injection (`Depends(get_db)`)
- Path/query parameters
- Request/response validation with Pydantic
- Exception handling (HTTPException)

**Why This Structure:**
Separates HTTP logic from business logic. Makes testing easier and keeps concerns isolated.

---

#### **`app/api/auth.py`** - Authentication Routes
**Purpose:** OAuth 2.0 login flow.

**Endpoints:**
- `POST /api/auth/login` - Initiate OAuth, return Google auth URL
- `GET /api/auth/callback` - Google redirects here with auth code
- `GET /api/auth/status` - Check if user is authenticated
- `POST /api/auth/logout` - Clear session

**Key Concepts to Study:**
- OAuth 2.0 authorization code flow
- Google API client library
- Token management
- Redirect responses

**Flow:**
1. Frontend calls POST `/auth/login`
2. Backend generates Google auth URL
3. Frontend opens popup with that URL
4. User authorizes on Google
5. Google redirects to `/auth/callback?code=...`
6. Backend exchanges code for token
7. Backend saves token locally
8. Frontend detects popup closed, reloads

---

### Models Layer (`app/models/`)

SQLAlchemy ORM models that represent database tables.

#### **`app/models/email.py`** - Email Model
**Purpose:** Define email table structure and relationships.

**Key Concepts to Study:**
- SQLAlchemy declarative models
- Column types (String, DateTime, Integer, Boolean, Text)
- Primary keys and foreign keys
- Relationships (one-to-many, cascade delete)
- Default values and constraints

**Important Fields:**
```python
class Email(Base):
    id: int              # Unique identifier
    gmail_message_id: str # ID from Gmail API
    gmail_thread_id: str  # Thread ID for reply detection
    to: str              # Recipient email
    subject: str         # Email subject
    body_text: str       # Plain text version
    body_html: str       # HTML version
    sent_at: datetime    # When sent
    send_count: int      # How many times resent
    responded: bool      # Has reply been detected?
    responded_at: datetime
    responded_source: str # "gmail" or "manual"
    last_checked_at: datetime
    attachments: relationship  # List of EmailAttachment objects
```

**Why This Matters:**
- `gmail_message_id` and `gmail_thread_id` link to Gmail API
- `send_count` tracks resends
- `responded` and `responded_source` show reply status
- Relationships enable automatic cascade deletion

---

#### **`app/models/email_attachment.py`** - Attachment Model
**Purpose:** Store metadata about email attachments.

**Fields:**
```python
class EmailAttachment(Base):
    id: int
    email_id: int        # Foreign key to Email
    filename: str
    mime_type: str       # "application/pdf", "image/png", etc
    size_bytes: int
    storage_path: str    # Local filesystem path
    disposition: str     # "attachment" or "inline"
    content_id: str      # For inline images (cid:xxx)
```

**Why Separate Table:**
One email can have multiple attachments. Normalization prevents data duplication.

---

#### **`app/models/template.py`** - Template Model
**Purpose:** Store email templates with placeholders.

**Fields:**
```python
class Template(Base):
    id: int
    name: str
    subject_template: str      # "Hello {{company}}"
    body_text_template: str
    body_html_template: str
    placeholders: relationship  # List of TemplatePlaceholder
```

**Relationship:**
One template has many placeholders. Allows dynamic form generation.

---

### Schemas Layer (`app/schemas/`)

Pydantic models for request/response validation.

#### **`app/schemas/email.py`** - Email Schemas
**Purpose:** Validate incoming requests and serialize database models to JSON.

**Key Schemas:**
```python
# Request: what client sends
class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body_text: str | None
    body_html: str | None
    attachments: list[EmailAttachmentIn]

# Response: what API returns
class EmailSendResponse(BaseModel):
    id: int
    to: str
    sent_at: datetime
    send_count: int
    
    class Config:
        from_attributes = True  # Convert SQLAlchemy model to dict

# History item for list responses
class EmailHistoryItem(BaseModel):
    id: int
    to: str
    subject: str
    sent_at: datetime
    send_count: int
    responded: bool
    relative_time: str  # "2 hours ago"
    status_emoji: str   # "🟡"
```

**Key Concepts to Study:**
- Pydantic validation (type hints, Field constraints)
- Request/response serialization
- `from_attributes = True` (ORM mode) for model conversion
- Field constraints (min_length, max_length, ge, le)

**Why Separate from Models:**
- Models represent database schema
- Schemas represent API contract
- Different concerns: persistence vs. data transfer

---

### Services Layer (`app/services/`)

Business logic and orchestration. Services call models, external APIs, and databases.

#### **`app/services/email_service.py`** - Email Business Logic
**Purpose:** Core functionality (create, send, resend, check replies).

**Key Functions:**

**`create_email(db, data, gmail_message_id, gmail_thread_id)`**
- Inserts email and attachments into database
- Called after successful Gmail send

**`list_history(db, limit, offset)`**
- Fetches paginated email history
- Calculates status emoji based on time thresholds
- Returns formatted response

**`resend_email(db, email_id)`**
- Fetches original email from DB
- Calls Gmail API to send (via `send_email_via_gmail`)
- Updates sent_at and send_count
- Resets responded status

**`check_reply(db, email_id)`**
- Fetches email and its Gmail thread ID
- Calls Gmail API to get thread
- Detects if new messages arrived after sent_at
- Updates responded status if reply found

**Key Concepts to Study:**
- Transaction management (db.commit, db.refresh)
- Query building with SQLAlchemy (db.get, db.query, filters)
- External API integration (calling Gmail service)
- Error handling and validation

**Why Services Matter:**
- Decouples API routes from business logic
- Makes logic reusable (can call same service from different routes)
- Easier to test (mock external dependencies)

---

#### **`app/services/template_service.py`** - Template Logic
**Purpose:** Template CRUD and placeholder handling.

**Key Concepts:**
- Regex for placeholder detection (`{{key}}` pattern)
- Template substitution
- Dynamic form generation

---

### Gmail Integration (`app/gmail/`)

External API wrappers for Gmail.

#### **`app/gmail/gmail_client.py`** - Gmail Authentication
**Purpose:** Manage OAuth tokens and build authenticated Gmail service.

**Key Functions:**

**`get_valid_credentials()`**
- Loads token from `backend/secrets/token.json`
- Checks if expired
- Refreshes if needed
- Returns credentials object

**`get_gmail_service()`**
- Calls `get_valid_credentials()`
- Builds Google API client
- Returns authenticated service for API calls

**Key Concepts to Study:**
- Google Auth library (google-auth)
- Token refresh mechanism
- File I/O for token storage

**Why Separate:**
Centralizes all Gmail auth logic. Easy to add token refresh, caching, error handling.

---

#### **`app/gmail/gmail_sender.py`** - Email Sending
**Purpose:** Build MIME messages and send via Gmail API.

**Key Function:**

**`build_email_message(to, subject, body_text, body_html, attachments)`**
- Creates RFC 2822 email structure
- Handles multipart (text + HTML + attachments + inline images)
- Sets proper headers (From, To, Subject, Message-ID)
- Returns MIMEMultipart object

**`send_email_via_gmail(service, to, subject, body_text, body_html, attachments)`**
- Calls `build_email_message()`
- Encodes as base64
- Calls Gmail API `messages.send()`
- Returns `{"gmail_message_id": "...", "gmail_thread_id": "..."}`

**Key Concepts to Study:**
- MIME (Multipurpose Internet Mail Extensions)
- RFC 2822 email format
- Email headers and structure
- Base64 encoding
- Gmail API messages.send endpoint

**Why This Matters:**
Gmail API requires RFC 2822 format. Understanding MIME is crucial for:
- Attachments
- Inline images
- Text + HTML alternatives
- Proper encoding

---

#### **`app/gmail/reply_detector.py`** - Reply Detection
**Purpose:** Detect if email has been replied to.

**Key Function:**

**`check_thread_for_reply(service, thread_id, sent_at)`**
- Fetches thread from Gmail API
- Iterates messages in thread
- Finds message from someone else after sent_at
- Returns `{"replied": True/False}`

**Logic:**
```
FOR each message in thread:
  IF message.date > sent_at AND message.from != user_email:
    RETURN replied = True
END FOR
RETURN replied = False
```

**Key Concepts to Study:**
- Gmail API threads.get endpoint
- Message parsing
- Timestamp comparison
- Thread vs. message distinction

---

### Database Layer (`app/db/`)

Database configuration and utilities.

#### **`app/db/database.py`** - Connection & Sessions
**Purpose:** Configure SQLite connection and provide session management.

**Key Concepts to Study:**
- SQLAlchemy engine creation
- Database URL (sqlite:///db.sqlite)
- Session factories
- Connection pooling

---

#### **`app/db/deps.py`** - Dependency Injection
**Purpose:** Provide database session to routes.
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Usage in routes:**
```python
def send_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    # db is automatically injected
```

**Why This Pattern:**
- Automatic session cleanup
- Consistent database access
- Testable (can inject mock)

---

### Core Utilities (`app/core/`)

#### **`app/core/config.py`** - Configuration
**Purpose:** Load environment variables.

**Key Variables:**
- `GOOGLE_OAUTH_CLIENT_SECRETS_FILE` - Path to credentials.json
- `GOOGLE_OAUTH_TOKEN_FILE` - Path to token.json
- `GOOGLE_OAUTH_REDIRECT_URI` - Callback URL
- `GOOGLE_OAUTH_SCOPES` - Gmail API permissions

**Why Externalized:**
Different configs for dev/prod without changing code.

---

#### **`app/core/time_utils.py`** - Time Formatting
**Purpose:** Format relative time ("2 hours ago") and calculate status emojis.

**Functions:**
- `format_relative_time(dt)` - Returns "2 hours ago"
- `pick_status_emoji(minutes, thresholds)` - Returns ⚪🔵🟡🔴 based on time

---

### Migrations (`alembic/`)

#### **What is Alembic?**
Version control for database schema.

**Key Files:**
- `alembic/versions/` - Each file is a migration step
- `alembic/env.py` - Migration configuration
- `alembic.ini` - CLI configuration

**Example Migration:**
```python
def upgrade():
    op.add_column('emails', sa.Column('send_count', sa.Integer(), ...))

def downgrade():
    op.drop_column('emails', 'send_count')
```

**Key Concepts to Study:**
- Database versioning
- Schema evolution
- Backward compatibility
- `alembic upgrade head` / `alembic downgrade`

**Why Migrations Matter:**
- Track schema changes in git
- Deploy to production safely
- Rollback if needed
- Team coordination

---

## Data Flow: Sending an Email
```
Frontend (compose.js)
    |
    └─► POST /api/emails/send-multipart
        ↓
    EmailRouter (api/emails.py::send_email_multipart)
        |
        ├─► get_gmail_service() [gmail_client.py]
        │   └─► Returns authenticated Gmail service
        |
        ├─► send_email_via_gmail() [gmail_sender.py]
        │   ├─► build_email_message() [Creates MIME message]
        │   ├─► messages.send() [Gmail API call]
        │   └─► Returns {gmail_message_id, gmail_thread_id}
        |
        └─► create_email() [email_service.py]
            ├─► INSERT into emails table
            ├─► INSERT into email_attachments table
            ├─► db.commit()
            └─► Returns EmailSendResponse

    Response
        |
        └─► Frontend updates history view
```

---

## Data Flow: Checking for Replies
```
Frontend (history.js)
    |
    └─► POST /api/emails/{id}/check-reply
        ↓
    EmailRouter (api/emails.py::check_reply_now)
        |
        ├─► check_reply() [email_service.py]
        │   |
        │   ├─► db.get(Email, email_id)
        │   ├─► get_gmail_service()
        │   ├─► check_thread_for_reply() [reply_detector.py]
        │   │   ├─► threads.get(thread_id) [Gmail API]
        │   │   ├─► Iterate messages
        │   │   └─► Detect reply
        │   |
        │   ├─► UPDATE email.responded = True
        │   ├─► UPDATE email.responded_at = now()
        │   └─► db.commit()
        |
        └─► Response {responded: True/False, ...}

    Frontend
        |
        └─► Update history with 🟢 emoji if replied
```

---

## What to Study: Technology Prerequisites

### 1. **FastAPI & Web Frameworks** (2-3 days)
**Why:** Understand how HTTP requests are routed and responses are built.

**Topics:**
- Route decorators (`@app.post`, `@app.get`)
- Path & query parameters
- Request/response bodies
- Status codes
- Exception handling
- Middleware

**Resources:**
- FastAPI official tutorial: https://fastapi.tiangolo.com/
- Real Python FastAPI articles

---

### 2. **Pydantic & Data Validation** (1-2 days)
**Why:** Understand how data is validated before reaching business logic.

**Topics:**
- Type hints
- Field validation
- Custom validators
- ORM mode (`from_attributes`)
- JSON serialization

**Resources:**
- Pydantic docs: https://docs.pydantic.dev/

---

### 3. **SQLAlchemy & ORM** (3-4 days)
**Why:** Understand how Python objects map to database tables.

**Topics:**
- Declarative models
- Column types & constraints
- Relationships (one-to-many, foreign keys)
- Query building
- Sessions & transactions
- Cascade delete

**Resources:**
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Real Python SQLAlchemy tutorial

---

### 4. **Alembic Migrations** (1 day)
**Why:** Understand how to safely evolve database schema.

**Topics:**
- Migration files
- Upgrade & downgrade
- Auto-generate migrations
- Reversible changes

**Resources:**
- Alembic docs: https://alembic.sqlalchemy.org/

---

### 5. **OAuth 2.0 & Authentication** (2 days)
**Why:** Understand the authentication flow.

**Topics:**
- OAuth 2.0 authorization code flow
- Authorization vs. authentication
- Token exchange
- Redirect URIs
- Scopes & permissions

**Resources:**
- OAuth.net: https://oauth.net/2/
- Google OAuth docs: https://developers.google.com/identity/protocols/oauth2

---

### 6. **Gmail API** (2-3 days)
**Why:** Understand how to send emails and detect replies.

**Topics:**
- Authentication with Gmail API
- Messages.send endpoint
- Messages.get endpoint
- Threads.get endpoint
- MIME message format
- Message IDs & thread IDs

**Resources:**
- Gmail API docs: https://developers.google.com/gmail/api
- RFC 2822: https://tools.ietf.org/html/rfc2822

---

### 7. **Email & MIME Format** (1-2 days)
**Why:** Understand email structure and attachments.

**Topics:**
- RFC 2822 email format
- MIME multipart messages
- Content-Type headers
- Base64 encoding
- Inline vs. attachment disposition
- Content-ID for inline images

**Resources:**
- RFC 2822: https://tools.ietf.org/html/rfc2822
- MIME RFC: https://tools.ietf.org/html/rfc2045

---

### 8. **Python Advanced** (1 week, ongoing)
**Topics:**
- Type hints & annotations
- Async/await (FastAPI uses it)
- Context managers (with statements)
- Generators & yields
- Dependency injection patterns

---

## How to Navigate the Codebase

### Starting Point
1. Read `app/main.py` - Understand app initialization
2. Read `app/api/emails.py` - See all available routes
3. Pick one route and trace it:
   - Route handler
   - Service layer call
   - Database query
   - Response

### Example: Trace `POST /api/emails/send-multipart`
1. Start: `api/emails.py::send_email_multipart()`
2. Calls: `get_gmail_service()` → `gmail_client.py`
3. Calls: `send_email_via_gmail()` → `gmail_sender.py`
4. Calls: `create_email()` → `services/email_service.py`
5. Uses: `Email` model → `models/email.py`
6. Uses: `EmailAttachment` model → `models/email_attachment.py`
7. Returns: `EmailSendResponse` schema → `schemas/email.py`

---

## Common Tasks & Where to Find Them

| Task | File | Function |
|------|------|----------|
| Add new email field | `models/email.py` + migration | Define Column |
| Add new API endpoint | `api/emails.py` | Add @router.post() |
| Change email sending logic | `services/email_service.py` | Modify send logic |
| Fix Gmail integration | `gmail/gmail_sender.py` | Modify MIME building |
| Change reply detection | `gmail/reply_detector.py` | Modify thread checking |
| Update database schema | `alembic/versions/` | Create migration |
| Add validation | `schemas/email.py` | Add Field constraints |

---

## Testing Strategy

### Unit Tests (for services)
```python
# tests/test_email_service.py
def test_create_email():
    # Mock database
    # Call create_email()
    # Assert email created with correct fields
```

### Integration Tests (for routes)
```python
# tests/test_emails_api.py
def test_send_email_endpoint(client):
    # POST /api/emails/send
    # Assert 201 response
    # Assert email in database
    # Assert Gmail API called
```

### Key Concepts to Test:
- Service logic (business rules)
- API responses (status codes, schema)
- Database state (data persisted)
- Gmail API calls (mocked)
- Error handling (invalid input, auth failures)

---

## Deployment Checklist

Before deploying to production:

- [ ] `credentials.json` and `token.json` NOT in git
- [ ] `.env` file with production values
- [ ] Database migrations ran (`alembic upgrade head`)
- [ ] Tests passing
- [ ] Error logging configured
- [ ] CORS configured for production domain
- [ ] Rate limiting implemented
- [ ] Input validation complete
- [ ] Gmail API credentials rotated if needed
- [ ] Database backed up

---

## Next Steps

1. **Learn the prerequisites** in order (FastAPI → Pydantic → SQLAlchemy)
2. **Trace one complete flow** (e.g., sending an email)
3. **Make a small change** (add a new field to Email model)
4. **Write a test** for your change
5. **Explore edge cases** (what if attachment is too large? what if Gmail API fails?)

Good luck! 🚀