# AI To-Do Email Automation Agent

Turn natural-language reminders into trackable tasks and Gmail drafts. The application uses an LLM to extract task details and write email drafts, while the backend validates dates, enforces approval, schedules approved sends, and records their outcomes.

> **Project status:** This README describes the proposed design. The project directory currently contains no implementation, so commands, endpoints, environment variables, and behavior below are a starting contract to implement and verify. Do not treat the examples as evidence that a feature is already available.

## Goals

- Capture reminders written in ordinary language.
- Extract a title, recipient, due date, and intent; ask the user to clarify missing or ambiguous details.
- Track tasks and due/overdue state.
- Generate editable email drafts.
- Send an email only after explicit user approval and only at the approved send time.
- Keep tasks, drafts, send attempts, and scheduled work recoverable across restarts.

## Features in the planned first version

- FastAPI backend and Streamlit user interface.
- Structured LLM extraction and email writing (provider to be selected).
- PostgreSQL persistence for application data using SQLAlchemy.
- Gmail API sending through Google OAuth 2.0.
- APScheduler 3.x for scheduled sends and periodic due-task checks.
- A persistent APScheduler job store backed by a separate SQLite file.
- Startup reconciliation for scheduled or interrupted work.
- Status transition validation and atomic send claiming to reduce duplicate sends.

## Architecture and workflow

```text
Streamlit UI
    │ HTTP (planned; API contract to be implemented)
    ▼
FastAPI ── LLM: extract and draft
    │
    ├── PostgreSQL / SQLAlchemy: tasks, drafts, send logs
    ├── APScheduler 3.x + separate SQLite job store: timed work
    └── Gmail API + OAuth: approved email delivery
```

1. The user submits a reminder.
2. The LLM extracts task fields. The backend validates the structured result and asks for clarification when required details are missing or ambiguous.
3. The task is saved as `pending`.
4. The LLM prepares an email draft; the task/draft moves to `draft_ready`.
5. The user edits the draft, explicitly approves it, and chooses to send now or later. The approved content and recipient are persisted; status becomes `approved`.
6. For a future send, the backend stores `send_at` in UTC, moves the item to `scheduled`, and registers a date-triggered scheduler job. “Send now” should use the same guarded sending path immediately.
7. When due, the job atomically claims the scheduled draft (`scheduled` → `sending`), rechecks current state and approval, sends through Gmail, and records `sent` or `failed` plus a send log.
8. A recurring job identifies tasks that are due or overdue. It should flag/update task state or surface them in the UI; it must not send an unapproved email.

The LLM proposes structured content and dates; it does not authorize or send email. Backend validation and the persisted approval are authoritative.

## Status lifecycle

Define the statuses and transition map centrally (planned: `src/todo_agent/domain/status.py`) and reject transitions outside that map. The design names these transitions:

| From | To | Meaning |
|---|---|---|
| `pending` | `draft_ready` | Details are sufficient and a draft has been generated. |
| `draft_ready` | `approved` | User approved the current edited draft and selected a send time. |
| `approved` | `scheduled` | Future send time was persisted and its job registered. |
| `scheduled` | `sending` | A worker successfully claimed the draft for sending. |
| `sending` | `sent` | Gmail accepted the send request and the result was recorded. |
| `sending` | `failed` | The send attempt failed or its result needs recovery. |
| `failed` | `scheduled` | Explicit retry after reviewing/reconciling the failure. |
| `pending`, `draft_ready`, `approved`, `scheduled` | `rejected` | User rejected the task/draft or cancelled before sending. |

The exact source states for `rejected`, cancellation semantics, and whether a rejected task is terminal should be made explicit in the implementation. Rescheduling should update the saved UTC time and replace the existing job. Cancellation should remove the job and invalidate the scheduled state. Never edit a draft after approval without requiring approval again.

## Technology stack

| Area | Planned choice |
|---|---|
| Language/runtime | Python 3.12 |
| API | FastAPI, Uvicorn |
| UI | Streamlit, HTTPX |
| Data validation/settings | Pydantic, pydantic-settings |
| Application database | PostgreSQL via SQLAlchemy (driver and migrations to choose) |
| Scheduling | APScheduler `>=3,<4`, `AsyncIOScheduler`, `SQLAlchemyJobStore` on a separate SQLite file |
| Email | Gmail API, Google OAuth client libraries |
| LLM | Provider to choose (for example Gemini, Anthropic, or OpenAI); use structured output and keep provider calls behind an adapter |
| Date parsing | `dateparser` plus Python timezone support (`tzdata` where needed) |
| Development | `pytest`, `pytest-asyncio`, `httpx`, Ruff, mypy, optional pre-commit and freezegun |

Pin compatible versions in `pyproject.toml`/`uv.lock`. APScheduler 4 has a different API and is outside this design.

## Planned folder structure

```text
ai-todo-email-agent/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── LICENSE
├── CHANGELOG.md
├── README.md
├── src/todo_agent/
│   ├── config.py
│   ├── main.py
│   ├── db.py
│   ├── dates.py
│   ├── api/
│   │   ├── routes_tasks.py
│   │   ├── routes_drafts.py
│   │   └── schemas.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── status.py
│   │   └── service.py
│   ├── llm/
│   │   ├── client.py
│   │   ├── prompts.py
│   │   ├── extractor.py
│   │   └── email_writer.py
│   ├── gmail/
│   │   ├── auth.py
│   │   └── sender.py
│   └── scheduling/
│       ├── scheduler.py
│       └── jobs.py
├── app/ui.py
├── scripts/auth_gmail.py
├── eval/
├── tests/
└── docs/
```

This is the proposed layout, not a listing of files that currently exist. Database models, API route names, OAuth callback flow, UI-to-API contract, and migration tooling remain to be implemented.

## Prerequisites

- Python 3.12.
- [`uv`](https://docs.astral.sh/uv/) installed and available on your `PATH`.
- PostgreSQL running locally or a reachable PostgreSQL database.
- A Google Cloud project with the Gmail API enabled and OAuth consent configured.
- Credentials for one selected LLM provider.
- A timezone name for interpreting user-entered local times (for example, `Africa/Nairobi`).

## Install and set up with uv

From the repository root, create the package and pin Python if those files do not already exist:

```bash
uv init --package ai-todo-email-agent
uv python pin 3.12
```

If the project files already exist, skip initialization and use `uv sync`. Add the planned dependencies (choose **one** LLM provider and adapt its client code):

```bash
uv add fastapi "uvicorn[standard]" pydantic pydantic-settings
uv add sqlalchemy "apscheduler>=3,<4" dateparser tzdata
uv add google-api-python-client google-auth-oauthlib google-auth-httplib2
uv add streamlit httpx

# Choose one provider, then implement/configure its adapter:
uv add google-genai
# or: uv add anthropic
# or: uv add openai

uv add --dev pytest pytest-asyncio ruff mypy freezegun
uv sync
```

The PostgreSQL SQLAlchemy driver is intentionally left open: select and add a compatible driver (for example, `psycopg`) when the database connection strategy is implemented. Add a migration tool such as Alembic if schema migrations are adopted.

## Environment configuration

Copy `.env.example` to `.env` and fill it with your own local values. Never commit `.env`, Google credential/token files, or real API keys. The variable names below are a proposed settings contract and must match `config.py` when implemented.

```dotenv
# Application
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO

# PostgreSQL application database; replace with your own database URL.
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE

# APScheduler 3.x persistent job store: separate SQLite file from app database.
SCHEDULER_JOBSTORE_URL=sqlite:///./jobs.sqlite
SCHEDULER_TIMEZONE=UTC
SCHEDULER_MISFIRE_GRACE_SECONDS=3600

# User's IANA timezone for interpreting natural-language local times.
DEFAULT_TIMEZONE=Africa/Nairobi

# Select and configure one provider. Leave unused provider keys empty.
LLM_PROVIDER=google
GOOGLE_API_KEY=
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
LLM_MODEL=

# Gmail OAuth files are created/downloaded through Google Cloud Console.
# Keep both files outside source control and restrict filesystem access.
GOOGLE_OAUTH_CLIENT_FILE=credentials.json
GOOGLE_OAUTH_TOKEN_FILE=token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.send

# Streamlit UI target (name/path to confirm when UI is implemented).
API_BASE_URL=http://127.0.0.1:8000
```

The PostgreSQL URL format depends on the selected SQLAlchemy driver. Use a secret manager and encrypted token storage for any deployed or shared environment. A local plaintext token file is only a development placeholder.

## Gmail OAuth setup

1. In Google Cloud Console, create/select a project and enable the Gmail API.
2. Configure the OAuth consent screen for the intended user audience. Keep the requested scope narrow; the proposed send-only scope is `https://www.googleapis.com/auth/gmail.send`.
3. Create an OAuth client appropriate to the implemented flow (desktop/local development or web application). If using a web client, configure its exact redirect URI in Google Cloud and in the app.
4. Download the OAuth client JSON and save it at the path configured by `GOOGLE_OAUTH_CLIENT_FILE`. Do not commit it.
5. Implement/run the one-time authorization script (planned: `scripts/auth_gmail.py`) to obtain a token. Store the token at `GOOGLE_OAUTH_TOKEN_FILE`, exclude it from version control, and protect it as a secret.
6. Confirm token refresh and revoked/expired credential behavior. The backend must revalidate the current draft's persisted approval immediately before sending.

Google may require consent-screen verification or test-user configuration depending on how the app is published and which scopes are requested. The exact OAuth flow and deployment callback URL are implementation-specific.

## Run locally

After the API module and UI file have been implemented:

```bash
uv run uvicorn todo_agent.main:app --reload --workers 1
```

In a second terminal:

```bash
uv run streamlit run app/ui.py
```

Use one API worker in this design because the scheduler is started in the FastAPI lifespan. Uvicorn reload is for local development only: reloads stop and restart the scheduler, so startup reconciliation must restore persisted scheduled jobs. For deployment, run a single scheduler-owning API process or move scheduling into a separately coordinated service before scaling API workers.

The Streamlit module path, API URLs, authentication, and CORS settings are not yet defined; align the UI and backend before treating these commands as verified.

## Testing and code quality

Planned commands:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Test the transition map, ambiguous/missing-date clarification, UTC conversion, atomic scheduler claim, approval checks, cancellation/rescheduling, startup reconciliation, misfires, Gmail failures, and retry behavior. Mock Gmail and the LLM in automated tests; test against real provider accounts only in an explicitly controlled environment. Use a fixed clock for date-dependent tests where practical. These commands will work once test/configuration files and implementation exist.

## Scheduling and operational constraints

- **APScheduler version:** use APScheduler 3.x (`apscheduler>=3,<4`); do not mix with 4.x examples.
- **Persistent job store:** use `SQLAlchemyJobStore` with a separate SQLite file (for example `jobs.sqlite`) so scheduler writes do not compete with application database writes. This provides job persistence across normal restarts, but does not make a single-host SQLite deployment highly available or horizontally scalable.
- **Serializable jobs:** persistent jobs must reference importable module-level functions and simple arguments such as `draft_id`. Avoid lambdas, nested functions, and bound methods. The job should reload authoritative data from the application database.
- **One scheduler owner:** run one scheduler instance/process. Multiple API worker processes each starting a scheduler can execute the same work. A multi-instance deployment needs a single scheduler service or a distributed coordination/queue design.
- **Date jobs:** schedule one date-triggered job per draft, with a stable ID such as `send-{draft_id}` and `replace_existing=True`. Rescheduling replaces it; cancellation removes it.
- **Misfires:** configure a bounded `misfire_grace_time` (the example is one hour) and `coalesce=True`. Decide and document what happens when a send is later than the grace window.
- **Startup recovery:** reconcile application records with scheduler jobs on startup. Re-register valid `scheduled` records; inspect records stuck in `sending` before retrying. Do not blindly resend uncertain outcomes.
- **Shutdown:** start and stop the scheduler through FastAPI's lifespan and shut it down cleanly.
- **SQLite limits:** do not share a local SQLite job-store file across hosts or assume it provides distributed locking. Back it up and protect it like other application data.

## UTC and timezone handling

- Require or configure an IANA timezone for interpreting local expressions such as “tomorrow at 9”. Pass a reference “now” and that timezone to the extractor; do not let the model guess the current date.
- Ask for clarification when the date/time or timezone is ambiguous. Validate parsed values in backend code and reject or clarify nonexistent/ambiguous daylight-saving times according to a documented policy.
- Convert accepted instants to timezone-aware UTC before persistence. Store `send_at` in UTC; run the scheduler in UTC. Preserve the user's timezone separately when needed for display and future recurring rules.
- Display times in the user's configured timezone, including the timezone label. Avoid naive datetimes and machine-local timezone defaults.

## Approval and duplicate-send safeguards

- Sending requires an explicit, persisted approval for the exact recipient, subject, body, and scheduled time. Editing after approval invalidates approval and requires the user to approve again.
- Immediately before sending, reload the draft and verify that it remains scheduled, approved, and not cancelled or already sent.
- Claim the record with one conditional database update, conceptually `UPDATE ... SET status='sending' WHERE id=:id AND status='scheduled'`. Proceed only if exactly one row was updated. Use a database transaction and appropriate concurrency controls.
- Record a send log and provider response identifiers where available. Keep failed and ambiguous outcomes visible for review.
- The conditional claim prevents two workers from acting on the same scheduled row at once, but Gmail sending and a local database transaction are not one atomic operation. If the process crashes after Gmail accepts the message but before `sent` is committed, exactly-once delivery cannot be guaranteed by this design alone. Reconciliation should flag uncertain sends for review instead of automatically retrying. Add provider-supported idempotency or an outbox/reconciliation strategy if stronger guarantees are required.
- Never allow an LLM response or a scheduler job alone to authorize a send.

## Security and privacy

- Keep API keys, OAuth client secrets, refresh tokens, and database credentials out of source control and logs.
- Request only the Gmail scopes required; protect token files locally and encrypt persisted tokens in a deployed system.
- Validate LLM output as untrusted input. Validate recipient addresses, content size, dates, and any action parameters server-side.
- Avoid sending more personal/task data to the LLM than necessary; disclose provider data handling in the app before real use.
- Add user authentication and authorization before exposing this service beyond a private local environment. The design does not yet specify multi-user isolation.

## Limitations and assumptions to resolve

- No implementation exists in this project context yet; paths, commands, and configuration names are proposed.
- Select one LLM provider/model and define structured schemas, retry/error policy, and data-retention behavior.
- Confirm the PostgreSQL driver, migrations, schema, and application connection lifecycle.
- Define API endpoints, UI interaction contract, authentication, and whether Streamlit calls the API over HTTP.
- Decide the OAuth client type, redirect flow, token encryption/storage, deployment consent model, and account ownership model.
- Clarify whether due/overdue processing only flags tasks or also creates a new draft/reminder. It must not send without approval.
- Define cancellation/rejection transitions and the policy for ambiguous provider send results.
- APScheduler plus a local SQLite job store is intended for a single-process prototype, not a multi-host high-availability scheduler.
- This design handles scheduled email and task reminders; attachment handling, recurring tasks, multiple mail providers, and multi-tenant authorization are not specified.

## Roadmap

1. Create package/configuration, database models, migrations, and centralized transition rules.
2. Implement task CRUD and structured extraction with a clarification flow.
3. Generate editable drafts and enforce approval in the service layer.
4. Add Gmail OAuth, token protection, send logging, and controlled test coverage.
5. Add APScheduler jobs, atomic claims, cancellation/rescheduling, and startup reconciliation.
6. Build the Streamlit UI for task review, draft editing, approval, schedule selection, and send status.
7. Add operational documentation, a short demo, provider failure handling, and a deployment design appropriate to the expected number of workers.

## License

No license has been selected.