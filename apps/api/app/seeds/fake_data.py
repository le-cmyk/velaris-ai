"""Seed fake client data for a new workspace."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_data import ClientDataRecord


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


async def seed_fake_client_data(workspace_id: uuid.UUID, db: AsyncSession) -> None:
    """Create sample client data records for a newly created workspace."""
    now = datetime.now(timezone.utc)
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
