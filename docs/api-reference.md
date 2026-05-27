# Velaris AI API Reference

Base URL: `http://localhost:8000`

## Authentication

All endpoints (except /auth/login and /health) require a ****** in the Authorization header.

```
Authorization: ******
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
