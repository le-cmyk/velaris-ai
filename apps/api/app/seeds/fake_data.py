"""Seed fake data for a new workspace — covers all rich-data-platform tables."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_template import AgentTemplate
from app.models.client_data import ClientDataRecord
from app.models.contact import Contact
from app.models.customer import Customer
from app.models.dashboard import Dashboard
from app.models.dashboard_widget import DashboardWidget
from app.models.deal import Deal
from app.models.invoice import Invoice
from app.models.product import Product
from app.models.support_ticket import SupportTicket
from app.models.task import Task
from app.models.ticket_comment import TicketComment


# ---------------------------------------------------------------------------
# Legacy ClientDataRecord seed (kept for backwards compatibility)
# ---------------------------------------------------------------------------

_FAKE_RECORDS: list[dict] = [
    # customers
    {
        "type": "customer",
        "title": "Acme Corporation",
        "content": "Long-term enterprise customer. Renewal due Q3. Primary contact: John Doe (john@acme.com).",
        "metadata_": {"plan": "enterprise", "mrr": 4500, "status": "active", "since": "2022-01-15"},
    },
    {
        "type": "customer",
        "title": "Blue Sky Ventures",
        "content": "Mid-market SaaS company. Evaluating upgrade to Pro plan. Champion: Sarah Lee.",
        "metadata_": {"plan": "pro", "mrr": 899, "status": "active", "since": "2023-06-01"},
    },
    {
        "type": "customer",
        "title": "Redwood Analytics",
        "content": "Startup customer. Using free tier. High-touch onboarding in progress.",
        "metadata_": {"plan": "free", "mrr": 0, "status": "trial", "since": "2024-03-10"},
    },
    # invoices
    {
        "type": "invoice",
        "title": "INV-2024-0042 – Acme Corporation",
        "content": "Annual enterprise subscription. $54,000 due 2024-04-01.",
        "metadata_": {
            "amount": 54000,
            "currency": "USD",
            "status": "paid",
            "due_date": "2024-04-01",
            "customer": "Acme Corporation",
        },
    },
    {
        "type": "invoice",
        "title": "INV-2024-0051 – Blue Sky Ventures",
        "content": "Monthly Pro plan subscription.",
        "metadata_": {
            "amount": 899,
            "currency": "USD",
            "status": "overdue",
            "due_date": "2024-05-01",
            "customer": "Blue Sky Ventures",
        },
    },
    # support tickets
    {
        "type": "support_ticket",
        "title": "TICKET-108: API rate limits being hit during bulk sync",
        "content": "Customer: Acme Corporation. Priority: high. Reported: 2024-04-18. "
        "Root cause under investigation – likely inefficient pagination in client SDK.",
        "metadata_": {"priority": "high", "status": "open", "customer": "Acme Corporation", "assignee": "eng-team"},
    },
    {
        "type": "support_ticket",
        "title": "TICKET-112: SSO login broken after password policy change",
        "content": "Customer: Blue Sky Ventures. Priority: medium. Workaround provided. Permanent fix in next release.",
        "metadata_": {
            "priority": "medium",
            "status": "in_progress",
            "customer": "Blue Sky Ventures",
            "assignee": "support",
        },
    },
    # tasks
    {
        "type": "task",
        "title": "Prepare Acme QBR presentation",
        "content": "Quarterly business review slides covering usage stats, ROI analysis, and roadmap preview. Due 2024-06-15.",
        "metadata_": {"status": "in_progress", "due_date": "2024-06-15", "owner": "csm-team"},
    },
    {
        "type": "task",
        "title": "Follow up on Blue Sky upgrade proposal",
        "content": "Send pricing comparison and case studies. Schedule demo of advanced analytics features.",
        "metadata_": {"status": "pending", "due_date": "2024-05-30", "owner": "sales-team"},
    },
    {
        "type": "task",
        "title": "Onboard Redwood Analytics",
        "content": "Complete 3-session onboarding. Session 1 done. Sessions 2 & 3 to be scheduled.",
        "metadata_": {"status": "in_progress", "due_date": "2024-06-01", "owner": "csm-team"},
    },
    # contracts
    {
        "type": "contract",
        "title": "Acme Corporation – Enterprise Agreement 2024",
        "content": "3-year enterprise contract. $54k/year. Auto-renews unless 90-day notice given. Signed 2024-01-01.",
        "metadata_": {
            "value": 162000,
            "currency": "USD",
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "status": "active",
        },
    },
    {
        "type": "contract",
        "title": "Blue Sky Ventures – Pro Plan MSA",
        "content": "Month-to-month Pro plan. Includes SLA for 99.9% uptime. Can upgrade to annual for 20% discount.",
        "metadata_": {
            "value": 10788,
            "currency": "USD",
            "start_date": "2023-06-01",
            "end_date": None,
            "status": "active",
        },
    },
    # company notes
    {
        "type": "company_note",
        "title": "Acme – Competitive threat: TechRival launch",
        "content": "TechRival launched a competing product targeting Acme's vertical. Need to accelerate roadmap items "
        "around data export and custom reporting to retain account.",
        "metadata_": {"tags": ["competitive", "retention", "roadmap"]},
    },
    {
        "type": "company_note",
        "title": "Team capacity note – May 2024",
        "content": "Engineering at 85% capacity this sprint. New hire starting June 3. Support coverage thin during "
        "May 20-24 due to team off-site.",
        "metadata_": {"tags": ["internal", "capacity", "hiring"]},
    },
    # product usage data
    {
        "type": "product_usage",
        "title": "Acme Corporation – April 2024 Usage",
        "content": "API calls: 1.2M (up 18% MoM). Active seats: 42/50. Data processed: 320GB. "
        "Top feature: bulk export (used daily).",
        "metadata_": {
            "api_calls": 1200000,
            "active_seats": 42,
            "total_seats": 50,
            "data_gb": 320,
            "month": "2024-04",
        },
    },
    {
        "type": "product_usage",
        "title": "Blue Sky Ventures – April 2024 Usage",
        "content": "API calls: 87k. Active seats: 5/10. Dashboard logins: 142. Low adoption – flag for CSM outreach.",
        "metadata_": {
            "api_calls": 87000,
            "active_seats": 5,
            "total_seats": 10,
            "data_gb": 14,
            "month": "2024-04",
        },
    },
]


# ---------------------------------------------------------------------------
# Comprehensive workspace seed
# ---------------------------------------------------------------------------

async def seed_workspace_data(workspace_id: uuid.UUID, db: AsyncSession) -> None:
    """Populate all rich-data-platform tables for a newly created workspace."""
    now = datetime.now(timezone.utc)
    today = date.today()

    # ── Customers ────────────────────────────────────────────────────────────
    customers_data = [
        dict(name="Acme Corporation",   status="active",   tier="enterprise", mrr=12000, churn_risk_score=0.10, industry="SaaS",          email="contact@acme.com"),
        dict(name="Blue Sky Ventures",  status="active",   tier="pro",        mrr=2400,  churn_risk_score=0.25, industry="FinTech",        email="hello@bluesky.io"),
        dict(name="Redwood Analytics",  status="at_risk",  tier="starter",    mrr=600,   churn_risk_score=0.72, industry="Healthcare",     email="info@redwoodanalytics.com"),
        dict(name="Pinnacle Tech",      status="active",   tier="enterprise", mrr=8500,  churn_risk_score=0.15, industry="Manufacturing",  email="contact@pinnacletech.com"),
        dict(name="Vertex Solutions",   status="prospect", tier=None,         mrr=0,     churn_risk_score=0.50, industry="Retail",         email="sales@vertexsolutions.com"),
        dict(name="CloudNine SaaS",     status="active",   tier="pro",        mrr=1800,  churn_risk_score=0.30, industry="SaaS",           email="support@cloudnine.io"),
        dict(name="DataStream Inc",     status="churned",  tier="starter",    mrr=0,     churn_risk_score=0.95, industry="Logistics",      email="info@datastream.com"),
        dict(name="Fusion Labs",        status="active",   tier="starter",    mrr=450,   churn_risk_score=0.45, industry="BioTech",        email="hello@fusionlabs.bio"),
        dict(name="Meridian Corp",      status="at_risk",  tier="pro",        mrr=3200,  churn_risk_score=0.68, industry="Real Estate",    email="contact@meridiancorp.com"),
        dict(name="Orbit Systems",      status="active",   tier="enterprise", mrr=15000, churn_risk_score=0.05, industry="Defense",        email="procurement@orbitsystems.com"),
    ]

    customer_objs: list[Customer] = []
    for i, cd in enumerate(customers_data):
        c = Customer(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            name=cd["name"],
            email=cd["email"],
            status=cd["status"],
            tier=cd["tier"],
            mrr=cd["mrr"],
            churn_risk_score=cd["churn_risk_score"],
            industry=cd["industry"],
            tags=[],
            created_at=now - timedelta(days=400 - i * 30),
            updated_at=now - timedelta(days=10 - i),
        )
        db.add(c)
        customer_objs.append(c)
    await db.flush()

    # ── Contacts (2 per customer) ─────────────────────────────────────────────
    _contacts_data = [
        # Acme
        ("John Doe",        "john@acme.com",          "VP of Engineering",     True),
        ("Lisa Grant",      "lisa@acme.com",           "IT Director",           False),
        # Blue Sky
        ("Sarah Lee",       "sarah@bluesky.io",        "CTO",                   True),
        ("Marcus Webb",     "marcus@bluesky.io",       "Head of Finance",       False),
        # Redwood
        ("Amy Chen",        "amy@redwoodanalytics.com","CEO",                   True),
        ("Derek Hall",      "derek@redwoodanalytics.com","Data Lead",           False),
        # Pinnacle
        ("Tom Rivera",      "tom@pinnacletech.com",    "Operations Manager",    True),
        ("Priya Nair",      "priya@pinnacletech.com",  "Procurement Lead",      False),
        # Vertex
        ("James Ford",      "james@vertexsolutions.com","VP Sales",             True),
        ("Nina Patel",      "nina@vertexsolutions.com", "Business Analyst",     False),
        # CloudNine
        ("Ryan Kim",        "ryan@cloudnine.io",       "Product Manager",       True),
        ("Chloe Martin",    "chloe@cloudnine.io",      "Customer Success",      False),
        # DataStream
        ("Owen Brooks",     "owen@datastream.com",     "CEO",                   True),
        ("Tara Singh",      "tara@datastream.com",     "Finance Director",      False),
        # Fusion Labs
        ("Ethan Ross",      "ethan@fusionlabs.bio",    "Research Lead",         True),
        ("Mia Johnson",     "mia@fusionlabs.bio",      "Operations",            False),
        # Meridian
        ("Carl White",      "carl@meridiancorp.com",   "CFO",                   True),
        ("Sandra Lee",      "sandra@meridiancorp.com", "Account Manager",       False),
        # Orbit
        ("Victor Stone",    "victor@orbitsystems.com", "Director of Procurement",True),
        ("Rachel Burns",    "rachel@orbitsystems.com", "Contract Manager",      False),
    ]

    for idx, (name, email, role, is_primary) in enumerate(_contacts_data):
        customer = customer_objs[idx // 2]
        db.add(Contact(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            customer_id=customer.id,
            name=name,
            email=email,
            role=role,
            is_primary=is_primary,
            created_at=now - timedelta(days=380 - idx * 10),
            updated_at=now - timedelta(days=5),
        ))
    await db.flush()

    # ── Deals ─────────────────────────────────────────────────────────────────
    # Map customer name → object
    cmap = {c.name: c for c in customer_objs}

    deals_data = [
        dict(name="Acme Q3 Expansion",           stage="negotiation", value=48000,  probability=75,  customer="Acme Corporation",   close_date=today + timedelta(days=45)),
        dict(name="Pinnacle Enterprise Renewal",  stage="proposal",    value=102000, probability=60,  customer="Pinnacle Tech",       close_date=today + timedelta(days=30)),
        dict(name="Vertex Solutions Onboarding",  stage="discovery",   value=7200,   probability=30,  customer="Vertex Solutions",    close_date=today + timedelta(days=90)),
        dict(name="CloudNine Upgrade",            stage="closed_won",  value=21600,  probability=100, customer="CloudNine SaaS",      close_date=today - timedelta(days=10)),
        dict(name="Fusion Labs Pro Plan",         stage="proposal",    value=5400,   probability=55,  customer="Fusion Labs",         close_date=today + timedelta(days=20)),
        dict(name="Meridian Save Attempt",        stage="negotiation", value=38400,  probability=40,  customer="Meridian Corp",       close_date=today + timedelta(days=15)),
        dict(name="Orbit Systems Expansion",      stage="discovery",   value=180000, probability=20,  customer="Orbit Systems",       close_date=today + timedelta(days=120)),
        dict(name="DataStream Win-Back",          stage="discovery",   value=5400,   probability=15,  customer="DataStream Inc",      close_date=today + timedelta(days=60)),
    ]

    deal_objs: list[Deal] = []
    for i, dd in enumerate(deals_data):
        d = Deal(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            customer_id=cmap[dd["customer"]].id,
            name=dd["name"],
            value=dd["value"],
            stage=dd["stage"],
            probability=dd["probability"],
            close_date=dd["close_date"],
            tags=[],
            created_at=now - timedelta(days=60 - i * 5),
            updated_at=now - timedelta(days=i + 1),
        )
        db.add(d)
        deal_objs.append(d)
    await db.flush()

    # ── Invoices (15 total) ───────────────────────────────────────────────────
    invoices_data = [
        dict(invoice_number="INV-2024-001", customer="Acme Corporation",  amount=12000, status="paid",    due_date=today - timedelta(days=60), paid_days_ago=55,
             line_items=[{"description": "Platform License – Enterprise", "quantity": 1, "unit_price": 12000, "total": 12000}]),
        dict(invoice_number="INV-2024-002", customer="Acme Corporation",  amount=12000, status="paid",    due_date=today - timedelta(days=30), paid_days_ago=25,
             line_items=[{"description": "Platform License – Enterprise", "quantity": 1, "unit_price": 12000, "total": 12000}]),
        dict(invoice_number="INV-2024-003", customer="Acme Corporation",  amount=12000, status="sent",    due_date=today + timedelta(days=15), paid_days_ago=None,
             line_items=[{"description": "Platform License – Enterprise", "quantity": 1, "unit_price": 12000, "total": 12000}]),
        dict(invoice_number="INV-2024-004", customer="Blue Sky Ventures", amount=2400,  status="paid",    due_date=today - timedelta(days=45), paid_days_ago=40,
             line_items=[{"description": "Pro Plan – Monthly", "quantity": 1, "unit_price": 2000, "total": 2000}, {"description": "Analytics Add-on", "quantity": 1, "unit_price": 400, "total": 400}]),
        dict(invoice_number="INV-2024-005", customer="Blue Sky Ventures", amount=2400,  status="overdue", due_date=today - timedelta(days=10), paid_days_ago=None,
             line_items=[{"description": "Pro Plan – Monthly", "quantity": 1, "unit_price": 2000, "total": 2000}, {"description": "Analytics Add-on", "quantity": 1, "unit_price": 400, "total": 400}]),
        dict(invoice_number="INV-2024-006", customer="Redwood Analytics", amount=600,   status="paid",    due_date=today - timedelta(days=60), paid_days_ago=55,
             line_items=[{"description": "Starter Plan – Monthly", "quantity": 1, "unit_price": 600, "total": 600}]),
        dict(invoice_number="INV-2024-007", customer="Redwood Analytics", amount=600,   status="overdue", due_date=today - timedelta(days=5),  paid_days_ago=None,
             line_items=[{"description": "Starter Plan – Monthly", "quantity": 1, "unit_price": 600, "total": 600}]),
        dict(invoice_number="INV-2024-008", customer="Pinnacle Tech",     amount=8500,  status="paid",    due_date=today - timedelta(days=30), paid_days_ago=28,
             line_items=[{"description": "Enterprise License", "quantity": 1, "unit_price": 7500, "total": 7500}, {"description": "SSO Module", "quantity": 1, "unit_price": 1000, "total": 1000}]),
        dict(invoice_number="INV-2024-009", customer="Pinnacle Tech",     amount=8500,  status="sent",    due_date=today + timedelta(days=20), paid_days_ago=None,
             line_items=[{"description": "Enterprise License", "quantity": 1, "unit_price": 7500, "total": 7500}, {"description": "SSO Module", "quantity": 1, "unit_price": 1000, "total": 1000}]),
        dict(invoice_number="INV-2024-010", customer="CloudNine SaaS",    amount=21600, status="paid",    due_date=today - timedelta(days=5),  paid_days_ago=3,
             line_items=[{"description": "Annual Pro Plan Upgrade", "quantity": 1, "unit_price": 18000, "total": 18000}, {"description": "Onboarding Services", "quantity": 1, "unit_price": 3600, "total": 3600}]),
        dict(invoice_number="INV-2024-011", customer="Fusion Labs",       amount=450,   status="paid",    due_date=today - timedelta(days=30), paid_days_ago=27,
             line_items=[{"description": "Starter Plan – Monthly", "quantity": 1, "unit_price": 450, "total": 450}]),
        dict(invoice_number="INV-2024-012", customer="Fusion Labs",       amount=450,   status="draft",   due_date=today + timedelta(days=30), paid_days_ago=None,
             line_items=[{"description": "Starter Plan – Monthly", "quantity": 1, "unit_price": 450, "total": 450}]),
        dict(invoice_number="INV-2024-013", customer="Meridian Corp",     amount=3200,  status="overdue", due_date=today - timedelta(days=20), paid_days_ago=None,
             line_items=[{"description": "Pro Plan – Monthly", "quantity": 1, "unit_price": 2800, "total": 2800}, {"description": "Support SLA Plus", "quantity": 1, "unit_price": 400, "total": 400}]),
        dict(invoice_number="INV-2024-014", customer="Orbit Systems",     amount=15000, status="paid",    due_date=today - timedelta(days=30), paid_days_ago=28,
             line_items=[{"description": "Enterprise License", "quantity": 1, "unit_price": 12000, "total": 12000}, {"description": "Data Export Tool", "quantity": 3, "unit_price": 1000, "total": 3000}]),
        dict(invoice_number="INV-2024-015", customer="Orbit Systems",     amount=15000, status="sent",    due_date=today + timedelta(days=10), paid_days_ago=None,
             line_items=[{"description": "Enterprise License", "quantity": 1, "unit_price": 12000, "total": 12000}, {"description": "Data Export Tool", "quantity": 3, "unit_price": 1000, "total": 3000}]),
    ]

    for i, inv in enumerate(invoices_data):
        paid_at = (now - timedelta(days=inv["paid_days_ago"])) if inv["paid_days_ago"] is not None else None
        db.add(Invoice(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            customer_id=cmap[inv["customer"]].id,
            invoice_number=inv["invoice_number"],
            amount=inv["amount"],
            status=inv["status"],
            due_date=inv["due_date"],
            paid_at=paid_at,
            line_items=inv["line_items"],
            created_at=now - timedelta(days=90 - i * 4),
            updated_at=now - timedelta(days=i + 1),
        ))
    await db.flush()

    # ── Support Tickets (10) ──────────────────────────────────────────────────
    tickets_data = [
        dict(ticket_number="TKT-001", customer="Acme Corporation",  subject="API rate limits hit during bulk sync",          body="Our bulk sync job is hitting rate limits. We need higher limits or guidance on batching.",   status="open",        priority="high",   assignee="eng-team"),
        dict(ticket_number="TKT-002", customer="Acme Corporation",  subject="Custom report export failing for large datasets",body="Reports > 100k rows time out. Getting 504 errors on the export endpoint.",                   status="in_progress", priority="high",   assignee="eng-team"),
        dict(ticket_number="TKT-003", customer="Blue Sky Ventures", subject="SSO login broken after password policy change",  body="Users can't log in via SSO since the policy update. Workaround needed urgently.",            status="in_progress", priority="medium", assignee="support"),
        dict(ticket_number="TKT-004", customer="Redwood Analytics", subject="Onboarding checklist items not saving",          body="Several onboarding checklist items reset after page refresh. Affecting new user experience.", status="open",        priority="medium", assignee="support"),
        dict(ticket_number="TKT-005", customer="Pinnacle Tech",     subject="Billing discrepancy on last invoice",            body="Invoice INV-2024-008 shows incorrect seat count. Please review and issue a credit note.",     status="resolved",    priority="low",    assignee="billing"),
        dict(ticket_number="TKT-006", customer="CloudNine SaaS",    subject="Dashboard widgets not loading after upgrade",    body="After the CloudNine plan upgrade, three dashboard widgets show loading spinner indefinitely.", status="resolved",    priority="medium", assignee="support"),
        dict(ticket_number="TKT-007", customer="Fusion Labs",       subject="API key rotation breaking webhooks",             body="After rotating our API key, webhook deliveries started failing with 401 errors.",            status="open",        priority="high",   assignee="eng-team"),
        dict(ticket_number="TKT-008", customer="Meridian Corp",     subject="Account flagged for churn – need escalation",   body="Account health score dropped below threshold. Requesting immediate CSM escalation.",          status="open",        priority="high",   assignee="csm-team"),
        dict(ticket_number="TKT-009", customer="Orbit Systems",     subject="SAML configuration assistance needed",           body="Need help configuring SAML 2.0 SSO with our identity provider (Okta).",                     status="in_progress", priority="medium", assignee="solutions-eng"),
        dict(ticket_number="TKT-010", customer="DataStream Inc",    subject="Data export before account closure",             body="We are closing our account and need a full data export within 30 days.",                     status="resolved",    priority="low",    assignee="support"),
    ]

    ticket_objs: list[SupportTicket] = []
    for i, td in enumerate(tickets_data):
        resolved_at = (now - timedelta(days=2)) if td["status"] == "resolved" else None
        t = SupportTicket(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            customer_id=cmap[td["customer"]].id,
            ticket_number=td["ticket_number"],
            subject=td["subject"],
            body=td["body"],
            status=td["status"],
            priority=td["priority"],
            assignee=td["assignee"],
            tags=[],
            resolved_at=resolved_at,
            created_at=now - timedelta(days=30 - i * 2),
            updated_at=now - timedelta(days=i),
        )
        db.add(t)
        ticket_objs.append(t)
    await db.flush()

    # ── Ticket Comments (2 per first 3 tickets = 6 total) ────────────────────
    comments_data = [
        (0, "Sarah Chen",     "We've identified the issue as a missing retry backoff in the client SDK. A patch is being prepared.", False),
        (0, "John Doe",       "Thanks for the update. We'll hold off on the bulk sync until the patch is available.",                False),
        (1, "eng-team",       "Reproduced locally. The export query is missing pagination. Fix will be in next release.",            True),
        (1, "John Doe",       "Acknowledged. Please prioritize – our monthly reporting depends on this feature.",                   False),
        (2, "support",        "Temporary workaround: disable SSO and use email/password until fix is deployed.",                    False),
        (2, "Sarah Lee",      "Workaround applied. Waiting for permanent fix. This is blocking 3 team members.",                    False),
    ]

    for ticket_idx, author_name, body, is_internal in comments_data:
        db.add(TicketComment(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            ticket_id=ticket_objs[ticket_idx].id,
            author_name=author_name,
            body=body,
            is_internal=is_internal,
            created_at=now - timedelta(hours=48 - ticket_idx * 6),
        ))
    await db.flush()

    # ── Tasks (12) ────────────────────────────────────────────────────────────
    tasks_data = [
        dict(title="Prepare Acme QBR presentation",         description="Quarterly business review slides: usage stats, ROI, roadmap preview.",      status="in_progress", priority="high",   due_date=today + timedelta(days=14), assignee="csm-team",   linked_type="customer",  linked_key="Acme Corporation"),
        dict(title="Follow up on Blue Sky upgrade proposal", description="Send pricing comparison and case studies. Schedule advanced analytics demo.", status="todo",        priority="medium", due_date=today + timedelta(days=5),  assignee="sales-team", linked_type="deal",      linked_key="Acme Q3 Expansion"),
        dict(title="Onboard Redwood Analytics",              description="Complete 3-session onboarding. Sessions 2 & 3 to be scheduled.",             status="in_progress", priority="medium", due_date=today + timedelta(days=7),  assignee="csm-team",   linked_type="customer",  linked_key="Redwood Analytics"),
        dict(title="Resolve TKT-001 API rate issue",         description="Coordinate with eng-team on the rate limit patch deployment.",               status="in_progress", priority="high",   due_date=today + timedelta(days=2),  assignee="eng-team",   linked_type="ticket",    linked_key="TKT-001"),
        dict(title="Send credit note to Pinnacle Tech",      description="Issue credit note for billing discrepancy on INV-2024-008.",                 status="done",        priority="low",    due_date=today - timedelta(days=2),  assignee="billing",    linked_type=None,         linked_key=None),
        dict(title="Escalate Meridian Corp account",         description="Schedule executive call to address churn risk and present retention offer.", status="todo",        priority="high",   due_date=today + timedelta(days=3),  assignee="csm-team",   linked_type="customer",  linked_key="Meridian Corp"),
        dict(title="Configure Orbit SAML SSO",              description="Walk Orbit Systems through Okta SAML 2.0 configuration step by step.",       status="in_progress", priority="medium", due_date=today + timedelta(days=10), assignee="solutions-eng", linked_type="ticket", linked_key="TKT-009"),
        dict(title="Draft Vertex Solutions proposal",        description="Prepare discovery summary and initial pricing proposal for Vertex.",         status="todo",        priority="medium", due_date=today + timedelta(days=20), assignee="sales-team", linked_type="deal",      linked_key="Vertex Solutions Onboarding"),
        dict(title="DataStream data export",                 description="Fulfil data export request before account closure deadline.",                status="in_progress", priority="medium", due_date=today + timedelta(days=25), assignee="support",    linked_type="ticket",    linked_key="TKT-010"),
        dict(title="Review CloudNine widget fix",            description="Verify dashboard widget fix in staging before promoting to production.",     status="done",        priority="low",    due_date=today - timedelta(days=5),  assignee="eng-team",   linked_type=None,         linked_key=None),
        dict(title="Monthly revenue reconciliation",         description="Reconcile paid invoices against MRR figures for the month.",                 status="todo",        priority="medium", due_date=today + timedelta(days=8),  assignee="finance",    linked_type=None,         linked_key=None),
        dict(title="Update agent template prompts",          description="Review and refresh system prompts across all built-in agent templates.",     status="todo",        priority="low",    due_date=today + timedelta(days=30), assignee="product",    linked_type=None,         linked_key=None),
    ]

    # Build lookup maps for linked entities
    deal_name_map = {d.name: d for d in deal_objs}
    ticket_num_map = {t.ticket_number: t for t in ticket_objs}

    for i, td in enumerate(tasks_data):
        linked_entity_id: uuid.UUID | None = None
        linked_entity_type: str | None = td["linked_type"]

        if td["linked_key"] is not None:
            if td["linked_type"] == "customer" and td["linked_key"] in cmap:
                linked_entity_id = cmap[td["linked_key"]].id
            elif td["linked_type"] == "deal" and td["linked_key"] in deal_name_map:
                linked_entity_id = deal_name_map[td["linked_key"]].id
            elif td["linked_type"] == "ticket":
                tkt = next((t for t in ticket_objs if t.ticket_number == td["linked_key"]), None)
                if tkt:
                    linked_entity_id = tkt.id

        db.add(Task(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            title=td["title"],
            description=td["description"],
            status=td["status"],
            priority=td["priority"],
            due_date=td["due_date"],
            assignee=td["assignee"],
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
            tags=[],
            created_at=now - timedelta(days=20 - i),
            updated_at=now - timedelta(hours=i * 3 + 1),
        ))
    await db.flush()

    # ── Products (6) ──────────────────────────────────────────────────────────
    products_data = [
        dict(name="API Platform Basic",  sku="API-BASIC",      price=299,  category="Platform", description="Entry-level API platform access with standard rate limits."),
        dict(name="API Platform Pro",    sku="API-PRO",        price=899,  category="Platform", description="Pro-tier API platform with higher limits and advanced features."),
        dict(name="Analytics Add-on",    sku="ADD-ANALYTICS",  price=199,  category="Add-on",   description="Advanced analytics dashboards and reporting capabilities."),
        dict(name="SSO Module",          sku="MOD-SSO",        price=149,  category="Module",   description="Single sign-on integration module supporting SAML 2.0 and OAuth."),
        dict(name="Data Export Tool",    sku="TOOL-EXPORT",    price=99,   category="Tool",     description="Bulk data export tool with scheduling and format options."),
        dict(name="Support SLA Plus",    sku="SLA-PLUS",       price=499,  category="Service",  description="Priority support SLA with 4-hour response time and dedicated CSM."),
    ]

    for i, pd in enumerate(products_data):
        db.add(Product(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            name=pd["name"],
            sku=pd["sku"],
            description=pd["description"],
            price=pd["price"],
            category=pd["category"],
            inventory_count=9999,
            is_active=True,
            created_at=now - timedelta(days=365 - i * 10),
            updated_at=now - timedelta(days=30),
        ))
    await db.flush()

    # ── Agent Templates (6 built-in) ──────────────────────────────────────────
    templates_data = [
        dict(
            name="Customer Health Monitor",
            icon="🏥",
            category="crm",
            description="Monitors customer health metrics and surfaces churn risk.",
            system_prompt=(
                "You are a customer health monitoring agent. Your role is to analyze customer health metrics "
                "including MRR, churn risk scores, support ticket volume, and engagement data. "
                "Identify customers at risk of churning and recommend targeted retention actions. "
                "Summarize findings in a clear, prioritized report for the customer success team."
            ),
        ),
        dict(
            name="Invoice Collection Agent",
            icon="💰",
            category="finance",
            description="Finds overdue invoices and drafts collection messages.",
            system_prompt=(
                "You are a finance automation agent specializing in accounts receivable. "
                "Your job is to identify overdue invoices, calculate outstanding balances, and draft "
                "professional but firm collection messages tailored to each customer's relationship and history. "
                "Escalate invoices overdue by more than 30 days to the finance director."
            ),
        ),
        dict(
            name="Support Ticket Triage",
            icon="🎫",
            category="support",
            description="Prioritizes and routes incoming support tickets.",
            system_prompt=(
                "You are a support operations agent responsible for triaging incoming support tickets. "
                "Analyze each ticket's subject, body, customer tier, and historical context to assign "
                "appropriate priority (low/medium/high/critical) and route to the correct team. "
                "Ensure SLA targets are met and flag tickets at risk of breaching their SLA."
            ),
        ),
        dict(
            name="Weekly Sales Summary",
            icon="📊",
            category="analytics",
            description="Summarizes deal pipeline and revenue metrics each week.",
            system_prompt=(
                "You are a sales analytics agent. Every week, compile a summary of the deal pipeline "
                "including new deals created, stage progressions, closed-won revenue, and projected close dates. "
                "Highlight deals that are stalled or at risk, and compare performance against the previous week. "
                "Present data in a concise executive summary format."
            ),
        ),
        dict(
            name="Data Quality Audit",
            icon="🔍",
            category="operations",
            description="Identifies incomplete or inconsistent records across the platform.",
            system_prompt=(
                "You are a data quality agent. Scan all customer, contact, deal, and invoice records to identify "
                "completeness issues (missing emails, empty fields, null values where data is expected) and "
                "consistency problems (duplicate entries, mismatched statuses, orphaned records). "
                "Produce a prioritized audit report with specific records that need attention."
            ),
        ),
        dict(
            name="Renewal Forecast",
            icon="🔮",
            category="analytics",
            description="Forecasts upcoming contract renewals and renewal risk.",
            system_prompt=(
                "You are a renewal forecasting agent. Analyze customer contracts, MRR trends, health scores, "
                "and historical renewal data to forecast which accounts are due for renewal in the next 90 days. "
                "Segment accounts by renewal likelihood (high/medium/low) and provide recommended actions "
                "for each segment to maximize revenue retention."
            ),
        ),
    ]

    for i, at in enumerate(templates_data):
        db.add(AgentTemplate(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            name=at["name"],
            description=at["description"],
            icon=at["icon"],
            category=at["category"],
            system_prompt=at["system_prompt"],
            allowed_tools=[],
            is_active=True,
            is_builtin=True,
            version=1,
            created_at=now - timedelta(days=365 - i * 5),
            updated_at=now - timedelta(days=30),
        ))
    await db.flush()

    # ── Dashboard + Widgets ───────────────────────────────────────────────────
    dashboard = Dashboard(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        name="Overview",
        description="Default workspace dashboard with key business metrics.",
        is_default=True,
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(days=1),
    )
    db.add(dashboard)
    await db.flush()

    widgets_data = [
        dict(title="Total MRR",        widget_type="metric",     query='{"table":"customers","agg":"sum","field":"mrr","filter":{"status":"active"}}',                            position_x=0, position_y=0, width=2, height=2),
        dict(title="Active Customers", widget_type="metric",     query='{"table":"customers","agg":"count","filter":{"status":"active"}}',                                        position_x=2, position_y=0, width=2, height=2),
        dict(title="Open Tickets",     widget_type="metric",     query='{"table":"support_tickets","agg":"count","filter":{"status":"open"}}',                                    position_x=4, position_y=0, width=2, height=2),
        dict(title="Deal Pipeline",    widget_type="bar_chart",  query='{"table":"deals","group_by":"stage","agg":"sum","field":"value"}',                                        position_x=0, position_y=2, width=4, height=3),
        dict(title="Customer Health",  widget_type="table",      query='{"table":"customers","order_by":"mrr","limit":10}',                                                       position_x=4, position_y=2, width=4, height=3),
        dict(title="Revenue Overview", widget_type="line_chart", query='{"table":"invoices","group_by":"month","agg":"sum","field":"amount","filter":{"status":"paid"}}',         position_x=0, position_y=5, width=8, height=3),
    ]

    for i, wd in enumerate(widgets_data):
        db.add(DashboardWidget(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            dashboard_id=dashboard.id,
            title=wd["title"],
            widget_type=wd["widget_type"],
            data_source="query",
            query=wd["query"],
            config={},
            position_x=wd["position_x"],
            position_y=wd["position_y"],
            width=wd["width"],
            height=wd["height"],
            created_at=now - timedelta(days=29 - i),
            updated_at=now - timedelta(days=1),
        ))
    await db.flush()

    # ── Legacy ClientDataRecord seed ──────────────────────────────────────────
    for i, record in enumerate(_FAKE_RECORDS):
        created_at = now - timedelta(days=len(_FAKE_RECORDS) - i)
        db.add(
            ClientDataRecord(
                id=uuid.uuid4(),
                workspace_id=workspace_id,
                type=record["type"],
                title=record["title"],
                content=record.get("content"),
                metadata_=record.get("metadata_"),
                created_at=created_at,
                updated_at=created_at,
            )
        )
    await db.flush()


# Aliases for backwards compatibility
seed_fake_data = seed_workspace_data
seed_fake_client_data = seed_workspace_data
