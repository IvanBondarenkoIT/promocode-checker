from datetime import UTC, datetime

import pytest
from app.models import Campaign, CampaignStatus, Promocode
from app.services.campaign_import import close_campaign, import_campaign_rows, upsert_campaign
from sqlalchemy import select

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def test_upsert_campaign_and_import(db_session) -> None:
    campaign = upsert_campaign(
        db_session,
        code="beans_wave_test",
        name="Coffee beans test wave",
        starts_at=datetime(2026, 8, 1, tzinfo=UTC),
        ends_at=datetime(2026, 8, 31, tzinfo=UTC),
        notes="unit test",
    )
    assert campaign.status == CampaignStatus.ACTIVE

    rows = [
        {"customer_erp_id": "C1", "promocode": "11000001"},
        {"customer_erp_id": "C2", "promocode": "11000002"},
        {"customer_erp_id": "C3", "promocode": "bad"},
    ]
    inserted, skipped, errors = import_campaign_rows(
        db_session, campaign=campaign, rows=rows, ttl_days=30
    )
    assert inserted == 2
    assert skipped == 0
    assert len(errors) == 1

    inserted2, skipped2, errors2 = import_campaign_rows(
        db_session, campaign=campaign, rows=rows[:2], ttl_days=30
    )
    assert inserted2 == 0
    assert skipped2 == 2
    assert errors2 == []

    codes = db_session.scalars(
        select(Promocode.promocode).where(Promocode.campaign_id == campaign.id)
    ).all()
    assert sorted(codes) == ["11000001", "11000002"]


def test_close_campaign(db_session) -> None:
    campaign = upsert_campaign(
        db_session,
        code="old_wave",
        name="Old wave",
        starts_at=None,
        ends_at=None,
        notes=None,
    )
    closed = close_campaign(db_session, "old_wave")
    assert closed is not None
    assert closed.status == CampaignStatus.CLOSED
    assert db_session.get(Campaign, campaign.id).status == CampaignStatus.CLOSED
