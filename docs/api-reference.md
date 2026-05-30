# Velaris AI API Reference

Base URL: `http://localhost:8000`

## Authentication

All endpoints except `/auth/login`, `/auth/signup`, `/health`, and `/api/health` require a bearer token in the Authorization header.

```
Authorization: Bearer <token>
```

## Endpoints

### POST /auth/login
Login and receive a JWT token.

**Request:**
```json
{ "email": "demo@velaris.ai", "password": "demo123" }
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "workspace_id": "uuid",
  "email": "demo@velaris.ai"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{ "status": "ok", "version": "0.1.0" }
```

### GET /workspace
Get workspace information.

### GET /backend/capabilities
Return the backend services Velaris can provide to clients and future agents.

**Response:**
```json
{
  "capabilities": [
    {
      "name": "backend_blueprints",
      "description": "Turn a client request into routes, data objects, infrastructure, and implementation steps.",
      "entrypoints": ["GET /backend/capabilities", "POST /backend/blueprints"]
    }
  ]
}
```

### POST /backend/blueprints
Convert a client explanation, optional route list, optional data objects, and infrastructure needs into a backend implementation plan.

**Request:**
```json
{
  "description": "We need a customer support backend with tickets, customers, dashboards, and scheduled syncs.",
  "requested_routes": [
    { "method": "GET", "path": "/support/tickets", "purpose": "List tickets", "auth_required": true }
  ],
  "data_entities": [
    { "name": "ticket", "fields": ["customer_id", "status", "priority"], "relationships": ["belongs to customer"] }
  ],
  "infrastructure": ["worker"]
}
```

**Response:**
```json
{
  "summary": "Velaris can provide this as a workspace-scoped backend...",
  "routes": [
    {
      "method": "GET",
      "path": "/support/tickets",
      "purpose": "List tickets",
      "auth_required": true,
      "workspace_scoped": true,
      "status": "proposed",
      "handler": null
    }
  ],
  "data_objects": [
    {
      "name": "ticket",
      "backing_table": "support_tickets",
      "fields": ["customer_id", "status", "priority"],
      "relationships": ["belongs to customer"],
      "status": "available"
    }
  ],
  "infrastructure": [],
  "implementation_steps": [],
  "open_questions": []
}
```

### GET /backend/endpoints
List runtime endpoints created for the current workspace.

### POST /backend/endpoints
Create a runtime client-specific endpoint. These routes are available immediately under `/client-api`.

**Agent-backed endpoint request:**
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

**Deterministic read endpoint request:**
```json
{
  "name": "Active Customers API",
  "method": "GET",
  "path": "/customers/active",
  "mode": "data_query",
  "description": "Dedicated client route for active customers",
  "config": {
    "table": "customers",
    "select": ["id", "name", "email", "status"],
    "filters": [{ "field": "status", "op": "eq", "value": "active" }],
    "allowed_filter_fields": ["country", "tier"],
    "limit": 100
  }
}
```

**Write endpoint request:**
```json
{
  "name": "Create Lead",
  "method": "POST",
  "path": "/leads",
  "mode": "client_data_create",
  "config": {
    "type": "lead",
    "title_field": "company",
    "content_field": "notes",
    "metadata_field": "metadata"
  }
}
```

### PATCH /backend/endpoints/{endpoint_id}
Update endpoint metadata, config, or `is_active`.

### ANY /client-api/{path}
Execute a runtime endpoint for the authenticated workspace.

Example:

```text
POST /client-api/support/triage
GET /client-api/customers/active?country=US
POST /client-api/leads
```

In `agent_task` mode, `/client-api/{path}` creates an agent run and passes the endpoint contract, query params, body, allowed tools, and instructions into the agent. The route remains stable while the agent decides which Velaris data, system, tool, or function should fulfill the request.

### GET /data/catalog
Discover the Velaris data contract for the current workspace.

Optional query params:

```text
include_counts=true
```

**Response:**
```json
{
  "tables": [
    {
      "name": "customers",
      "description": "Accounts, companies, or people the workspace sells to or supports.",
      "workspace_scoped": true,
      "columns": [
        { "name": "id", "type": "UUID", "nullable": false, "primary_key": true, "indexed": false },
        { "name": "workspace_id", "type": "UUID", "nullable": false, "primary_key": false, "indexed": true, "foreign_key": "workspaces.id" }
      ],
      "default_sort": "updated_at",
      "row_count": 12
    }
  ],
  "relationships": [
    {
      "from_table": "deals",
      "from_column": "customer_id",
      "to_table": "customers",
      "to_column": "id",
      "on_delete": "SET NULL"
    }
  ]
}
```

### GET /data/relationships
Return only the relationship graph. Agents use this before deciding how to join or traverse client data.

### POST /data/query
Query Velaris-managed data with structured filters. Velaris always enforces the authenticated user's `workspace_id`; callers cannot override it.

**Request:**
```json
{
  "table": "customers",
  "select": ["id", "name", "email", "status", "mrr"],
  "filters": [
    { "field": "status", "op": "eq", "value": "active" },
    { "field": "name", "op": "ilike", "value": "acme" }
  ],
  "sort": { "field": "updated_at", "direction": "desc" },
  "limit": 50,
  "offset": 0
}
```

**Response:**
```json
{
  "table": "customers",
  "columns": ["id", "name", "email", "status", "mrr"],
  "rows": [
    { "id": "uuid", "name": "Acme", "email": "ops@acme.test", "status": "active", "mrr": 1000.0 }
  ],
  "row_count": 1,
  "limit": 50,
  "offset": 0
}
```

### POST /chat
Send a message to the AI agent.

**Request:**
```json
{
  "message": "Show me the list of customers",
  "workspace_id": "uuid"
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "message": "Here are the customers in your database...",
  "intent": "database_read",
  "execution_plan": ["classify_intent", "generate_query", "execute_query", "format_response"],
  "tool_calls": [...],
  "pending_approvals": [],
  "status": "completed"
}
```

### GET /runs/{run_id}
Get details of an agent run.

### GET /approvals
List pending approval requests.

### POST /approvals/{approval_id}/approve
Approve a pending action.

### POST /approvals/{approval_id}/reject
Reject a pending action.

### GET /audit-logs
Get paginated audit logs.

### GET /tools
List available tools.
