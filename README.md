# Radium Backend

FastAPI + PostgreSQL backend for the Radium public site (`radium-client`) and
admin console (`radium-admin`).

**Stack:** Python 3.12+ · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL · Alembic ·
Pydantic v2 · JWT (access + rotating refresh tokens) · bcrypt · slowapi

## Quick start

Requires a PostgreSQL server you can already connect to (local install or a
remote one) and Python 3.12+.

```bash
cp .env.example .env
# edit .env: POSTGRES_HOST/PORT/USER/PASSWORD/DB to match your PostgreSQL,
# and set SECRET_KEY: openssl rand -hex 32

pip install -r requirements-dev.txt

# create the database first if it doesn't exist yet, e.g.:
#   psql -h <host> -p <port> -U <user> -c "CREATE DATABASE radium;"

alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

- API: http://localhost:8000/api/v1
- Swagger: http://localhost:8000/docs (disabled when `APP_ENV=production`)

On this machine dependencies are installed for the system Python
(`pip install --user --break-system-packages -r requirements.txt`, since this
Debian install blocks plain `pip install` — PEP 668), so `uvicorn`/`alembic`
work directly from any shell with no activation step.

**On a machine without that override**, use an isolated virtualenv instead —
safer, and the normal recommendation:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

If `python3 -m venv` fails with `ensurepip is not available` (some
Debian/Ubuntu builds strip it out and need `apt install python3.12-venv`,
which requires sudo), bootstrap pip manually instead:

```bash
python3 -m venv .venv --without-pip
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python /tmp/get-pip.py
.venv/bin/pip install -r requirements-dev.txt
```

## Default credentials

Seeded superuser (matches the demo credentials shown by the radium-admin login
page): `admin@radium.example` / `radium@2026`. Change them via
`FIRST_SUPERUSER_*` in `.env` before deploying anywhere real.

## Project structure

```
app/
├── main.py            # app factory, middleware, mounts
├── core/              # config, security (JWT/bcrypt), logging, exceptions, rate limit
├── db/                # engine/session, declarative base + mixins, seed
├── models/            # SQLAlchemy models (UUID PKs, timestamps, soft delete)
├── schemas/           # Pydantic request/response schemas + envelope
├── repositories/      # data access (generic base: pagination/search/sort/filter)
├── services/          # business logic (auth, users, email)
├── api/
│   ├── deps.py        # DB session, current user, RBAC dependencies
│   └── v1/            # versioned routers and endpoints
├── middleware/        # request-id logging, security headers
├── storage/           # file storage abstraction (local now; S3 etc. later)
└── utils/             # pagination params, helpers
alembic/               # migrations (async env)
```

## API conventions

Every success response uses one envelope:

```json
{ "success": true, "message": "OK", "data": …, "meta": { "page": 1, … } }
```

Errors (any status) use:

```json
{ "success": false, "message": "…", "errors": [{ "field": "…", "message": "…" }] }
```

List endpoints accept `page`, `page_size`, `sort_by`, `order`, `search`, plus
endpoint-specific filters.

### Auth

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/login` | email + password → access & refresh tokens + user |
| `POST /api/v1/auth/refresh` | rotate the refresh token (reuse ⇒ all sessions revoked) |
| `POST /api/v1/auth/logout` | revoke one refresh token |
| `POST /api/v1/auth/logout-all` | revoke every session |
| `GET /api/v1/auth/me` | current user |
| `POST /api/v1/auth/change-password` | verify current password, revoke sessions |
| `POST /api/v1/auth/forgot-password` | email-ready reset link (console backend logs it) |
| `POST /api/v1/auth/reset-password` | single-use token → new password |

Send the access token as `Authorization: Bearer <token>`.

### Wiring the radium-admin frontend

`radium-admin/src/services/auth.js` documents its swap contract. Map the login
response like so:

```js
const res = await fetch(`${API}/auth/login`, { method: 'POST', … })
const { data } = await res.json()
const session = {
  user: {
    name: data.user.full_name,
    email: data.user.email,
    role: data.user.role_display,   // "Administrator"
    initials: data.user.initials,   // "RA"
  },
  token: data.access_token,
  signedInAt: data.signed_in_at,
}
```

`data.user` itself is `{ id, email, full_name, role, role_display, initials,
is_active, last_login_at, created_at, updated_at }` — `role` is the machine
value (`"admin"`), `role_display` is the label the UI shows.

### File uploads

`POST /api/v1/media` (multipart, authenticated) stores the file and returns
`{ filename, path, url, size, content_type }`; files are served from
`/uploads/…`. The storage layer is an interface — S3/Supabase/Cloudinary are a
new backend class plus `STORAGE_BACKEND` config, with no API changes.

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

## Roles

RBAC roles: `admin`, `editor`, `viewer` (login response also exposes a display
name, e.g. "Administrator"). User management endpoints require `admin`.

## Running in production

Run the same commands as the quick start (migrate, seed, then start the
server) with a production-grade ASGI invocation instead of `--reload`, e.g.:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Behind a process manager (systemd, supervisor, etc.) is recommended so it
restarts on failure; put a reverse proxy (nginx/Caddy) in front for TLS.

## Environments

`APP_ENV=development` (default) enables docs and human-readable logs.
`APP_ENV=production` disables docs, logs JSON, and refuses to boot if
`SECRET_KEY`, `POSTGRES_PASSWORD`, or `FIRST_SUPERUSER_PASSWORD` are still at
their shipped default values.

## Deploying to Render

`.env` is gitignored on purpose and never reaches Render — set every key from
`.env.example` in the service's **Environment** tab instead (Dashboard →
your service → Environment). At minimum:

- `DATABASE_URL` — a reachable Postgres instance. Render's own Postgres add-on
  gives you a DSN starting `postgres://`; the app coerces that to
  `postgresql+asyncpg://` automatically, so paste it as-is. Prefer the
  **Internal Database URL** if the database is a Render Postgres in the same
  region (no TLS needed, lower latency) over the External one.
- `APP_ENV=production` — also makes the app refuse to boot with any default
  `SECRET_KEY` / `POSTGRES_PASSWORD` / `FIRST_SUPERUSER_PASSWORD`, so set
  those too.
- `SECRET_KEY`, `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD`.

Forgetting `DATABASE_URL` leaves `POSTGRES_HOST` at its `localhost` default,
which Render's container can't reach — the service still starts (uvicorn
doesn't need the database), but every DB-touching request throws
`ConnectionRefusedError` at connection time. A startup DB ping now fails the
deploy immediately with an actionable log line instead of only surfacing
this on a user's first login.

## Operational notes for a real deployment

- **Reverse proxy**: the app trusts `request.client` (the direct TCP peer),
  not `X-Forwarded-For`, unless `TRUST_PROXY_HEADERS=true`. Only set that
  behind a proxy you control that overwrites the header — otherwise clients
  can spoof it to dodge rate limits or poison the IP recorded on login
  sessions.
- **Database exposure**: make sure PostgreSQL itself isn't reachable from
  outside your network (firewall / `pg_hba.conf` / bind address) — this app
  has no control over that once it's pointed at an external database.
- **Uploads**: SVG is intentionally not in `ALLOWED_UPLOAD_EXTENSIONS` — an
  uploaded SVG can carry `<script>` and would execute when served inline from
  `/uploads`. Add it back only alongside sanitization or an
  `attachment`-disposition/CSP setup.
