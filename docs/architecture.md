# Velaris AI Architecture

## Overview

Velaris AI is a portable, client-deployable agentic AI platform.

## Architecture Diagram

```
Next.js Frontend (port 3000)
        ↓
FastAPI Backend API (port 8000)
        ↓
Backend Blueprint Planner (client needs → routes/data/infra plan)
        ↓
Runtime Client Endpoints (/backend/endpoints → /client-api/*)
        ↓
Agent Runtime (API request → tool/function/data orchestration)
        ↓
Velaris Data Backend (catalog, relationships, structured queries)
        ↓
Tool Gateway (security, approval, audit)
        ↓
MCP Tool Layer (postgres_query, ...)
        ↓
PostgreSQL / Redis
```

## Services

### Frontend (apps/web)
- Next.js 14 with App Router
- React + TypeScript
- Tailwind CSS + shadcn/ui components
- Communicates with backend via REST API

### Backend API (apps/api)
- FastAPI + Python 3.11
- SQLAlchemy 2.0 async ORM
- Alembic migrations
- JWT authentication
- Pydantic v2 schemas

### Backend Blueprint Planner
- Accepts natural-language client needs and explicit requested routes
- Maps known business objects to existing Velaris tables
- Proposes missing data objects, routes, and infrastructure
- Produces implementation steps and open questions for the next agent
- Audits blueprint creation per workspace

### Runtime Client Endpoints
- Agents can create client-specific endpoints without changing deployed Python code
- Endpoint definitions are stored per workspace in `client_endpoints`
- `/client-api/{path}` resolves the authenticated workspace, HTTP method, and active endpoint definition
- `agent_task` mode turns an API request into an agent run; there is no dedicated handwritten route handler
- `data_query` mode exposes dedicated read endpoints backed by the Velaris data backend
- `client_data_create` mode provides simple write endpoints into flexible client data records
- Every execution is workspace-scoped and audited

### Agent Runtime
- Intent classification (keyword-based for MVP)
- Execution planning
- Tool orchestration

### Velaris Data Backend
- Public data catalog for queryable workspace tables
- Relationship graph built from SQLAlchemy foreign keys
- Structured query endpoint for filters, sorting, pagination, and column selection
- Workspace isolation enforced server-side on every query
- JSON-safe serialization for UUIDs, datetimes, dates, and decimals

### Tool Gateway
- Security validation layer
- SQL safety checker (SELECT allowed, writes require approval)
- Audit logging for all tool calls
- Approval management

### MCP Tool Layer
- Mock MCP interface (MCP SDK-ready)
- data_query for workspace-scoped structured access
- postgres_query tool for deeper SQL diagnostics

## Database Schema

- users
- workspaces
- agent_runs
- tool_calls
- approval_requests
- audit_logs
- client_endpoints
- memories (pgvector-ready)
- customers, contacts, deals, invoices, support tickets, tasks, products
- conversations, messages, workflows, dashboards, notifications

## Security

- JWT authentication (HS256)
- Bcrypt password hashing
- Workspace isolation
- Read-only by default
- Approval workflow for risky actions
- Audit logs for all important actions

## Quick Start

See README.md for setup instructions.
