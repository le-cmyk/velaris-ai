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

Edit `.env` to set a strong `SECRET_KEY` for production. The defaults work for local development.

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

### 4. Log in

Open http://localhost:3000 and log in with the demo account:

| Field | Value |
|-------|-------|
| Email | `demo@velaris.ai` |
| Password | `demo123` |

### 5. Try it out

In the **Chat** interface, send a message like:

> Show me the list of customers in the database.

You will see:
- The assistant response
- The classified intent (`database_read`)
- The execution plan steps
- The tool call (`postgres_query`) and its result

Try a write request to trigger the approval workflow:

> Delete all inactive users.

This creates a pending approval in the **Approvals** panel that you can approve or reject.

---

## Architecture

```
Next.js Frontend (port 3000)
        ↓
FastAPI Backend API (port 8000)
        ↓
Agent Runtime  (intent classification → execution plan)
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
| `apps/web/` | Next.js 14 frontend — dashboard, chat, approvals, audit logs |
| `apps/api/` | FastAPI backend — all REST endpoints, JWT auth, migrations |
| `apps/api/app/agent/` | Agent runtime — intent classification, execution planning |
| `apps/api/app/gateway/` | Tool Gateway — SQL safety checker, approval enforcement |
| `apps/api/app/mcp/` | MCP-ready tool abstraction + mock `postgres_query` tool |
| `deployments/docker-compose/` | Docker Compose with init SQL |
| `packages/shared-types/` | Shared TypeScript types |
| `packages/prompts/` | System prompts for agents |
| `docs/` | Architecture and API reference |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/workspace` | Workspace info |
| POST | `/chat` | Send message to agent |
| GET | `/runs/{run_id}` | Get agent run details |
| GET | `/approvals` | List pending approvals |
| POST | `/approvals/{id}/approve` | Approve a pending action |
| POST | `/approvals/{id}/reject` | Reject a pending action |
| GET | `/audit-logs` | Paginated audit log |
| GET | `/tools` | List available tools |

Full Swagger UI available at http://localhost:8000/docs when running.

---

## Security

- **JWT authentication** — HS256 tokens, configurable expiry
- **Bcrypt password hashing** — all passwords hashed with passlib
- **Read-only by default** — only `SELECT` queries execute without approval
- **Approval workflow** — `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` require explicit human approval
- **Audit logs** — every login, tool call, and approval decision is logged
- **Workspace isolation** — all database tables include `workspace_id` for tenant separation
- **No hardcoded secrets** — all credentials from `.env`

---

## Client Configuration

Copy `client-config.example.yaml` to `client-config.yaml` to customise the deployment:

```yaml
client:
  name: my-company
  environment: production

security:
  readonly_by_default: true
  require_approval_for:
    - database_write
    - send_email

tools:
  postgres_query:
    enabled: true
    readonly: true

agents:
  - name: data_analyst
    enabled: true
    tools:
      - postgres_query
```

The backend loads this file at startup and merges it with safe defaults.

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
npm install --legacy-peer-deps

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

## Repository Structure

```
velaris-ai/
├── apps/
│   ├── web/                  # Next.js frontend
│   └── api/                  # FastAPI backend
│       ├── app/
│       │   ├── agent/        # Agent runtime
│       │   ├── gateway/      # Tool Gateway
│       │   ├── mcp/          # MCP tool layer
│       │   ├── models/       # SQLAlchemy ORM models
│       │   ├── routers/      # FastAPI route handlers
│       │   └── schemas/      # Pydantic request/response schemas
│       ├── alembic/          # Database migrations
│       └── tests/            # Unit tests
├── services/
│   ├── agent-runtime/        # (future) standalone agent service
│   ├── tool-gateway/         # (future) standalone gateway service
│   ├── mcp-servers/          # (future) real MCP server implementations
│   └── workers/              # (future) background workers
├── packages/
│   ├── shared-types/         # Shared TypeScript types
│   ├── prompts/              # Agent system prompts
│   └── evals/                # (future) evaluation harnesses
├── deployments/
│   └── docker-compose/       # Docker Compose + init SQL
├── docs/                     # Architecture and API reference
├── client-config.example.yaml
├── .env.example
└── docker-compose.yml        # Root-level convenience file
```

---

## Roadmap

- [ ] Real LLM integration (OpenAI / Anthropic)
- [ ] Real MCP SDK client/server connections
- [ ] pgvector embeddings for memory search
- [ ] Multi-agent collaboration
- [ ] Visual workflow builder
- [ ] Kubernetes / Helm deployment
- [ ] RBAC and SSO (Keycloak)
- [ ] OpenTelemetry observability

---

## Demo credentials

| Email | Password | Role |
|-------|----------|------|
| `demo@velaris.ai` | `demo123` | Admin |

> **Note:** Change the demo password and `SECRET_KEY` before any non-local deployment.
