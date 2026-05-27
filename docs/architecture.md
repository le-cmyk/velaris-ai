# Velaris AI Architecture

## Overview

Velaris AI is a portable, client-deployable agentic AI platform.

## Architecture Diagram

```
Next.js Frontend (port 3000)
        ↓
FastAPI Backend API (port 8000)
        ↓
Agent Runtime (intent classification, planning)
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

### Agent Runtime
- Intent classification (keyword-based for MVP)
- Execution planning
- Tool orchestration

### Tool Gateway
- Security validation layer
- SQL safety checker (SELECT allowed, writes require approval)
- Audit logging for all tool calls
- Approval management

### MCP Tool Layer
- Mock MCP interface (MCP SDK-ready)
- postgres_query tool

## Database Schema

- users
- workspaces
- agent_runs
- tool_calls
- approval_requests
- audit_logs
- memories (pgvector-ready)

## Security

- JWT authentication (HS256)
- Bcrypt password hashing
- Workspace isolation
- Read-only by default
- Approval workflow for risky actions
- Audit logs for all important actions

## Quick Start

See README.md for setup instructions.
