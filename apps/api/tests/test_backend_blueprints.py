from __future__ import annotations

from app.backend.blueprints import create_backend_blueprint, get_backend_capabilities
from app.schemas.backend_blueprint import BackendBlueprintRequest, RequestedEntity, RequestedRoute


def test_backend_capabilities_explain_entrypoints() -> None:
    capabilities = get_backend_capabilities()

    names = {capability.name for capability in capabilities.capabilities}
    assert "backend_blueprints" in names
    assert "data_backend" in names
    assert any(
        "POST /backend/blueprints" in capability.entrypoints
        for capability in capabilities.capabilities
    )


def test_blueprint_from_natural_language_need_maps_existing_data() -> None:
    blueprint = create_backend_blueprint(
        BackendBlueprintRequest(
            description="We need a customer support backend with tickets, customers, dashboards, and scheduled syncs.",
            infrastructure=["worker"],
        )
    )

    backing_tables = {item.backing_table for item in blueprint.data_objects}
    assert "customers" in backing_tables
    assert "support_tickets" in backing_tables
    assert any(route.path == "/data/catalog" and route.status == "available" for route in blueprint.routes)
    assert any(item.name == "Background Worker" for item in blueprint.infrastructure)


def test_blueprint_accepts_client_requested_routes_and_new_entities() -> None:
    blueprint = create_backend_blueprint(
        BackendBlueprintRequest(
            description="Client needs a custom backend for subscriptions.",
            requested_routes=[
                RequestedRoute(method="GET", path="/subscriptions", purpose="List subscriptions"),
                RequestedRoute(method="POST", path="/subscriptions", purpose="Create subscriptions"),
            ],
            data_entities=[
                RequestedEntity(
                    name="subscription",
                    fields=["customer_id", "plan", "status", "renews_at"],
                    relationships=["belongs to customer"],
                )
            ],
        )
    )

    assert any(route.path == "/subscriptions" and route.status == "proposed" for route in blueprint.routes)
    subscription = next(item for item in blueprint.data_objects if item.name == "subscription")
    assert subscription.status == "proposed"
    assert "Which proposed data objects need new database migrations?" in blueprint.open_questions
