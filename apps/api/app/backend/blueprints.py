from __future__ import annotations

from app.data.catalog import PUBLIC_DATA_MODELS
from app.schemas.backend_blueprint import (
    BackendBlueprintRequest,
    BackendBlueprintResponse,
    BackendCapabilitiesResponse,
    BackendCapability,
    BlueprintDataObject,
    BlueprintInfrastructureItem,
    BlueprintRoute,
)


_ENTITY_TABLE_ALIASES = {
    "account": "customers",
    "accounts": "customers",
    "agent": "agent_templates",
    "agents": "agent_templates",
    "company": "customers",
    "companies": "customers",
    "contact": "contacts",
    "contacts": "contacts",
    "conversation": "conversations",
    "conversations": "conversations",
    "customer": "customers",
    "customers": "customers",
    "dashboard": "dashboards",
    "dashboards": "dashboards",
    "deal": "deals",
    "deals": "deals",
    "invoice": "invoices",
    "invoices": "invoices",
    "message": "messages",
    "messages": "messages",
    "notification": "notifications",
    "notifications": "notifications",
    "product": "products",
    "products": "products",
    "scheduled job": "scheduled_jobs",
    "support": "support_tickets",
    "support ticket": "support_tickets",
    "ticket": "support_tickets",
    "tickets": "support_tickets",
    "task": "tasks",
    "tasks": "tasks",
    "workflow": "workflows",
    "workflows": "workflows",
}

_INFRASTRUCTURE = {
    "api": BlueprintInfrastructureItem(
        name="FastAPI API",
        purpose="Authenticated REST surface for agents, frontends, and services.",
        status="available",
    ),
    "postgres": BlueprintInfrastructureItem(
        name="PostgreSQL",
        purpose="Workspace-scoped relational data store with migrations.",
        status="available",
    ),
    "redis": BlueprintInfrastructureItem(
        name="Redis",
        purpose="Cache, queue, and short-lived coordination layer.",
        status="available",
    ),
    "docker": BlueprintInfrastructureItem(
        name="Docker Compose",
        purpose="Containerized local and deployable runtime for API, web, Postgres, and Redis.",
        status="available",
    ),
    "audit": BlueprintInfrastructureItem(
        name="Audit Logs",
        purpose="Durable trace of backend actions, data access, approvals, and agent operations.",
        status="available",
    ),
    "approval": BlueprintInfrastructureItem(
        name="Human Approvals",
        purpose="Approval workflow for destructive or externally risky actions.",
        status="available",
    ),
    "worker": BlueprintInfrastructureItem(
        name="Background Worker",
        purpose="Run long jobs, syncs, scheduled workflows, and outbound integrations.",
        status="recommended",
    ),
    "storage": BlueprintInfrastructureItem(
        name="Object Storage",
        purpose="Store files, exports, documents, and large binary assets outside Postgres.",
        status="recommended",
    ),
}


def get_backend_capabilities() -> BackendCapabilitiesResponse:
    return BackendCapabilitiesResponse(
        capabilities=[
            BackendCapability(
                name="backend_blueprints",
                description="Turn a client request into routes, data objects, infrastructure, and implementation steps.",
                entrypoints=[
                    "GET /backend/capabilities",
                    "POST /backend/blueprints",
                    "GET /backend/endpoints",
                    "POST /backend/endpoints",
                    "PATCH /backend/endpoints/{endpoint_id}",
                    "ANY /client-api/{path}",
                ],
            ),
            BackendCapability(
                name="data_backend",
                description="Discover data shape, inspect relationships, and query workspace-scoped records.",
                entrypoints=["GET /data/catalog", "GET /data/relationships", "POST /data/query"],
            ),
            BackendCapability(
                name="agent_gateway",
                description="Expose safe tools to agents with validation, approvals, and audit logs.",
                entrypoints=["GET /tools", "POST /chat"],
            ),
            BackendCapability(
                name="infrastructure",
                description="Run Velaris as a containerized backend stack with API, web, Postgres, and Redis.",
                entrypoints=["docker compose up --build", "GET /health", "GET /api/health"],
            ),
        ]
    )


def _normalize_entity_name(name: str) -> str:
    return " ".join(name.strip().lower().replace("_", " ").replace("-", " ").split())


def _table_for_entity(name: str) -> str | None:
    normalized = _normalize_entity_name(name)
    return _ENTITY_TABLE_ALIASES.get(normalized) or (
        normalized.replace(" ", "_") if normalized.replace(" ", "_") in PUBLIC_DATA_MODELS else None
    )


def _guess_entities(description: str) -> list[str]:
    lowered = description.lower()
    matches = []
    for alias, table in _ENTITY_TABLE_ALIASES.items():
        if alias in lowered and table not in matches:
            matches.append(table)
    return matches


def _default_routes_for_table(table: str) -> list[BlueprintRoute]:
    resource = table.replace("_records", "").replace("_", "-")
    return [
        BlueprintRoute(
            method="GET",
            path=f"/data/query?table={table}",
            purpose=f"List and filter {table}.",
            auth_required=True,
            workspace_scoped=True,
            status="available",
            handler="app.data.catalog.execute_data_query",
        ),
        BlueprintRoute(
            method="GET",
            path="/data/catalog",
            purpose=f"Inspect fields and relationships before querying {table}.",
            auth_required=True,
            workspace_scoped=True,
            status="available",
            handler="app.data.catalog.build_data_catalog",
        ),
        BlueprintRoute(
            method="POST",
            path=f"/{resource}",
            purpose=f"Create a dedicated write endpoint for {table} if structured writes are needed.",
            auth_required=True,
            workspace_scoped=True,
            status="proposed",
        ),
    ]


def _route_from_request(route) -> BlueprintRoute:
    return BlueprintRoute(
        method=route.method,
        path=route.path,
        purpose=route.purpose or f"Client requested {route.method} {route.path}.",
        auth_required=route.auth_required,
        workspace_scoped=route.auth_required,
        status="proposed",
    )


def create_backend_blueprint(request: BackendBlueprintRequest) -> BackendBlueprintResponse:
    tables = _guess_entities(request.description)
    data_objects: list[BlueprintDataObject] = []

    for entity in request.data_entities:
        table = _table_for_entity(entity.name)
        if table and table not in tables:
            tables.append(table)
        data_objects.append(
            BlueprintDataObject(
                name=entity.name,
                backing_table=table,
                fields=entity.fields,
                relationships=entity.relationships,
                status="available" if table else "proposed",
            )
        )

    for table in tables:
        if not any(item.backing_table == table for item in data_objects):
            data_objects.append(
                BlueprintDataObject(
                    name=table.replace("_", " "),
                    backing_table=table,
                    fields=[],
                    relationships=[],
                    status="available",
                )
            )

    routes: list[BlueprintRoute] = []
    seen_route_keys = set()
    for route in request.requested_routes:
        blueprint_route = _route_from_request(route)
        routes.append(blueprint_route)
        seen_route_keys.add((blueprint_route.method, blueprint_route.path))

    for table in tables:
        for route in _default_routes_for_table(table):
            key = (route.method, route.path)
            if key not in seen_route_keys:
                routes.append(route)
                seen_route_keys.add(key)

    requested_infra = {_normalize_entity_name(item) for item in request.infrastructure}
    infra = [
        _INFRASTRUCTURE["api"],
        _INFRASTRUCTURE["postgres"],
        _INFRASTRUCTURE["redis"],
        _INFRASTRUCTURE["docker"],
        _INFRASTRUCTURE["audit"],
        _INFRASTRUCTURE["approval"],
    ]
    for key, item in _INFRASTRUCTURE.items():
        if key in requested_infra and item not in infra:
            infra.append(item)

    if any(word in request.description.lower() for word in ("file", "upload", "document", "export")):
        infra.append(_INFRASTRUCTURE["storage"])
    if any(word in request.description.lower() for word in ("schedule", "sync", "background", "cron")):
        infra.append(_INFRASTRUCTURE["worker"])

    implementation_steps = [
        "Confirm the client-facing data objects and route names.",
        "Map each data object to an existing Velaris table or create a migration for proposed objects.",
        "Expose read access through /data/catalog and /data/query first.",
        "Add dedicated write routes only where the client needs a stable product API.",
        "Protect every route with JWT auth, workspace scoping, audit logs, and approval checks for risky actions.",
        "Update client-config.yaml so future agents know which tools and routes are enabled.",
    ]

    open_questions = []
    if not data_objects:
        open_questions.append("Which business objects should Velaris store or expose for this client?")
    if not request.requested_routes:
        open_questions.append("Does the client need dedicated REST routes, or is /data/query enough for the first version?")
    if any(item.status == "proposed" for item in data_objects):
        open_questions.append("Which proposed data objects need new database migrations?")

    return BackendBlueprintResponse(
        summary="Velaris can provide this as a workspace-scoped backend with discoverable data, safe agent queries, audited operations, and containerized infrastructure.",
        routes=routes,
        data_objects=data_objects,
        infrastructure=infra,
        implementation_steps=implementation_steps,
        open_questions=open_questions,
    )
