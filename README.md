# Velaris AI

> The agentic operating system for modern companies.

Velaris AI is a portable, client-deployable agentic AI platform. It allows companies to deploy their own isolated AI instance with a web interface, backend API, agent runtime, workflow execution layer, MCP-connected tools, secure database access, audit logs, and human approval before risky actions.

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the repository

```bash
git clone https://github.com/le-cmyk/velaris-ai.git
cd velaris-ai
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` to set your secrets:

| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Strong random secret for JWT signing |
| `OPENROUTER_API_KEY` | Your OpenRouter API key (server-side only) |
| `OPENROUTER_MODEL` | OpenRouter model ID (default: `deepseek/deepseek-r1-0528`) |

### 3. Start the platform

```bash
docker compose up --build
```

This starts:
| Service | URL |
|---------|-----|
| Web frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 4. Log in or sign up

Open http://localhost:3000 to sign up with a new account, or log in with the demo account:

| Field | Value |
|-------|-------|
| Email | `demo@velaris.ai` |
| Password | `demo123` |

**New users automatically receive a private workspace with seeded sample data** — customers, invoices, support tickets, tasks, contracts, company notes, and product usage records.

### 5. Try it out

Visit `/dashboard/data` to browse your seeded records. Then open the **Chat** interface and ask:

> List all my customers.

> Summarize the support tickets.

> Create a new task: "Follow up with Acme on renewal"

---

## Architecture

```
Next.js Frontend (port 3000)
        ↓
FastAPI Backend API (port 8000)
        ↓
Agent Runtime  (intent classification → OpenRouter LLM → action parsing)
        ↓
Velaris Data Backend (catalog → relationships → structured workspace queries)
        ↓
Client Data Layer (workspace-isolated records: customers, invoices, etc.)
        ↓
Tool Gateway   (security checks, approval enforcement, audit logging)
        ↓
MCP Tool Layer (postgres_query mock — MCP SDK-ready)
        ↓
PostgreSQL / Redis
```

### Key modules

| Path | Purpose |
|------|---------|
| `apps/web/` | Next.js 14 frontend — dashboard, chat, data, approvals, audit logs |
| `apps/api/` | FastAPI backend — all REST endpoints, JWT auth, migrations |
| `apps/api/app/agent/` | Agent runtime — OpenRouter LLM, action execution, intent classification |
| `apps/api/app/data/` | Data backend — table catalog, relationship map, structured workspace queries |
| `apps/api/app/llm/` | OpenRouter HTTP client |
| `apps/api/app/gateway/` | Tool Gateway — SQL safety checker, approval enforcement |
| `apps/api/app/mcp/` | MCP-ready tool abstraction + mock `postgres_query` tool |
| `apps/api/app/seeds/` | Fake client data seeder (runs on every new signup) |
| `deployments/docker-compose/` | Docker Compose with init SQL |
| `docs/` | Architecture and API reference |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/signup` | Sign up, creates workspace + seeds data, returns JWT |
| GET | `/backend/capabilities` | Discover what backend services Velaris can provide |
| POST | `/backend/blueprints` | Convert a client need or requested routes into a backend plan |
| GET | `/backend/endpoints` | List runtime client-specific endpoints |
| POST | `/backend/endpoints` | Create a runtime client-specific endpoint |
| PATCH | `/backend/endpoints/{id}` | Update or disable a runtime endpoint |
| ANY | `/client-api/{path}` | Execute a client-specific endpoint created at runtime |
| GET | `/workspace` | Workspace info |
| POST | `/chat` | Send message to agent (OpenRouter LLM) |
| GET | `/runs/{run_id}` | Get agent run details |
| GET | `/client-data` | List workspace records (filter by type/search) |
| GET | `/client-data/{id}` | Get a single record |
| POST | `/client-data` | Create a record |
| PATCH | `/client-data/{id}` | Update a record |
| DELETE | `/client-data/{id}?confirmed=true` | Delete a record (requires `confirmed=true`) |
| GET | `/data/catalog?include_counts=true` | Discover queryable tables, columns, and relationships |
| GET | `/data/relationships` | Inspect table relationships for agent planning |
| POST | `/data/query` | Query workspace-scoped data through structured filters |
| GET | `/approvals` | List pending approvals |
| POST | `/approvals/{id}/approve` | Approve a pending action |
| POST | `/approvals/{id}/reject` | Reject a pending action |
| GET | `/audit-logs` | Paginated audit log |
| GET | `/tools` | List available tools |

Full Swagger UI available at http://localhost:8000/docs when running.

---

## OpenRouter LLM setup

The chat agent uses [OpenRouter](https://openrouter.ai) as the LLM provider.

1. Create an account at https://openrouter.ai and get an API key.
2. Add to your `.env` (backend only):

```env
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=deepseek/deepseek-r1-0528
```

> **Important:** `OPENROUTER_API_KEY` is a **backend-only** variable. Never add it to `NEXT_PUBLIC_*` or the Vercel frontend. Only `NEXT_PUBLIC_API_URL` goes to Vercel.

To change the model, update `OPENROUTER_MODEL`. The model ID must be a valid [OpenRouter model slug](https://openrouter.ai/models).

---

## Signup flow

1. User visits `/signup` and fills in email, password, and optional name/workspace fields.
2. Backend creates a new `Workspace` with a unique slug.
3. Backend creates a `User` linked to that workspace.
4. Backend seeds ~16 fake client records across 7 categories.
5. A JWT is returned in the same format as login.
6. User is redirected to `/dashboard`.
7. All future data operations are isolated to this workspace.

---

## Security

- **JWT authentication** — HS256 tokens, configurable expiry
- **Bcrypt password hashing** — all passwords hashed with passlib
- **Workspace isolation** — all tables include `workspace_id`; users can only access their own workspace
- **Read-only by default** — only `SELECT` queries execute without approval
- **Approval workflow** — `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` require explicit human approval
- **Delete confirmation** — `/client-data/{id}` requires `confirmed=true` query param
- **Audit logs** — every login, signup, tool call, record create/update/delete, and approval decision is logged
- **No hardcoded secrets** — all credentials from `.env`
- **LLM key server-side only** — `OPENROUTER_API_KEY` never exposed to the frontend

---

## Environment variables

### Backend (Railway)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `JWT_SECRET` | ✅ | Secret key for JWT signing |
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API key |
| `OPENROUTER_MODEL` | | OpenRouter model (default: `deepseek/deepseek-r1-0528`) |
| `CORS_ORIGINS` | ✅ | Comma-separated list of allowed frontend origins |
| `ENVIRONMENT` | | `development` or `production` |
| `CLIENT_CONFIG_PATH` | | Path to client YAML config |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL (e.g., `https://your-api.railway.app`) |

> No other env vars should be set on Vercel. The LLM key stays on the backend.

---

## Client Configuration

Copy `client-config.example.yaml` to `client-config.yaml` to customise the deployment:

```yaml
client:
  name: my-company
  environment: production

tools:
  data_query:
    enabled: true

  postgres_query:
    enabled: true
```

The `data_query` tool is the preferred agent-facing interface because it enforces workspace isolation and uses structured filters instead of raw SQL. Keep `postgres_query` for deeper diagnostics and administrative workflows that need explicit SQL safety checks.

### Backend blueprints

Future clients or agents can start with plain language, explicit route requests, or both:

```json
{
  "description": "We need a customer support backend with tickets, customers, dashboards, and scheduled syncs.",
  "requested_routes": [
    { "method": "GET", "path": "/support/tickets", "purpose": "List tickets" }
  ],
  "data_entities": [
    { "name": "ticket", "fields": ["customer_id", "status", "priority"] }
  ],
  "infrastructure": ["worker"]
}
```

Velaris returns proposed routes, mapped data objects, infrastructure, implementation steps, and open questions. This gives future agents a stable handoff: explain the backend, inspect the blueprint, then implement only the missing pieces.

### Runtime client endpoints

When a client needs a dedicated route immediately, an agent can register it without redeploying Velaris:

```json
{
  "name": "Smart Support Triage",
  "method": "POST",
  "path": "/support/triage",
  "mode": "agent_task",
  "description": "Route an API request to a Velaris agent that performs the needed backend work",
  "config": {
    "instruction": "Triage the request, inspect existing customer/ticket data, create or update records when needed, and return the client-facing result.",
    "allowed_tools": ["data_query", "client_data_create"],
    "response": "Return JSON with status, ticket/customer references, and next action."
  }
}
```

That definition is executed at:

```text
POST /client-api/support/triage
```

In `agent_task` mode, there is no dedicated handwritten handler behind the route. Velaris creates an agent run with the endpoint contract, query params, request body, allowed tools, and instructions. The agent then chooses the right data, system, tool, or function to satisfy the API request.

For deterministic read endpoints, agents can register `data_query` routes:

```json
{
  "name": "Active Customers API",
  "method": "GET",
  "path": "/customers/active",
  "mode": "data_query",
  "description": "Dedicated client route for active customers",
  "config": {
    "table": "customers",
    "select": ["id", "name", "email", "status", "mrr"],
    "filters": [{ "field": "status", "op": "eq", "value": "active" }],
    "allowed_filter_fields": ["country", "tier"],
    "limit": 100
  }
}
```

That definition is executed at:

```text
GET /client-api/customers/active?country=US
```

For simple writes into flexible client data, agents can create `client_data_create` endpoints:

```json
{
  "name": "Create Lead",
  "method": "POST",
  "path": "/leads",
  "mode": "client_data_create",
  "config": {
    "type": "lead",
    "title_field": "company",
    "content_field": "notes"
  }
}
```

All runtime endpoints are authenticated, workspace-scoped, audited, and can be disabled through `PATCH /backend/endpoints/{id}`.

---

## Development

### Backend (FastAPI)

```bash
cd apps/api
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload

# Run tests
python -m pytest tests/ -v
```

### Frontend (Next.js)

```bash
cd apps/web
npm install

# Run dev server
npm run dev

# Build
npm run build
```

### Database migrations

```bash
cd apps/api
alembic upgrade head
```

---

## Deployment guides

- Railway backend/database/Redis: `docs/deployment-railway.md`
- Vercel frontend: `docs/deployment-vercel.md`
- Final validation checklist: `docs/deployment-checklist.md`

---

## Repository Structure

```
velaris-ai/
├── apps/
│   ├── web/                  # Next.js frontend
│   └── api/                  # FastAPI backend
│       ├── app/
│       │   ├── agent/        # Agent runtime (OpenRouter, action execution)
│       │   ├── gateway/      # Tool Gateway
│       │   ├── llm/          # OpenRouter HTTP client
│       │   ├── mcp/          # MCP tool layer
│       │   ├── models/       # SQLAlchemy ORM models
│       │   ├── routers/      # FastAPI route handlers
│       │   ├── schemas/      # Pydantic request/response schemas
│       │   └── seeds/        # Fake client data seeder
│       ├── alembic/          # Database migrations
│       └── tests/            # Unit tests
├── deployments/
│   └── docker-compose/
├── docs/
├── client-config.example.yaml
├── .env.example
└── docker-compose.yml
```

---

## Demo credentials

| Email | Password | Role |
|-------|----------|------|
| `demo@velaris.ai` | `demo123` | Admin |

> **Note:** Change the demo password and `JWT_SECRET` before any non-local deployment.
