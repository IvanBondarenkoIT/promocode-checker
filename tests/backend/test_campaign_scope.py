"""Campaign kind scope: cashier, reconcile and segment import."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import Settings
from app.integrations.erp.mock import MockErpAdapter
from app.integrations.erp.types import CoffeeSaleMatch
from app.jobs.reconcile import run_reconcile
from app.models import Campaign, CampaignKind, CampaignStatus, Promocode, PromocodeStatus
from app.schemas.cashier import CashierResult
from app.services.campaign_scope import get_active_kind, set_active_kind
from app.services.cashier import check_promocode, redeem_promocode
from app.services.segment_import import SegmentRow, import_segment, rollback_campaign_codes
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.backend.conftest import postgres_available

pytestmark = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL test database is not available on localhost:5433",
)


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        TELEGRAM_BOT_TOKEN="",
        PROMOCODE_TTL_DAYS="30",
        PROMO_ENFORCEMENT_MODE="enforce",
        PROMO_MIN_COFFEE_KG="2.0",
    )


def _campaign(db: Session, *, code: str, kind: CampaignKind, prefix: str | None = None) -> Campaign:
    campaign = Campaign(
        id=uuid.uuid4(),
        code=code,
        name=code,
        status=CampaignStatus.ACTIVE,
        kind=kind,
        code_prefix=prefix,
    )
    db.add(campaign)
    db.flush()
    return campaign


def _promo(db: Session, *, code: str, campaign: Campaign | None, customer: str) -> Promocode:
    now = datetime.now(UTC)
    promo = Promocode(
        id=uuid.uuid4(),
        customer_erp_id=customer,
        promocode=code,
        status=PromocodeStatus.ACTIVE,
        campaign_id=campaign.id if campaign else None,
        created_at=now,
        expires_at=now + timedelta(days=30),
    )
    db.add(promo)
    db.flush()
    return promo


def test_cashier_rejects_code_from_other_kind(db_session: Session) -> None:
    live = _campaign(db_session, code="live_wave", kind=CampaignKind.LIVE, prefix="5")
    _promo(db_session, code="51000001", campaign=live, customer="777")
    set_active_kind(db_session, CampaignKind.TEST)

    response = check_promocode(db_session, code="51000001", point_id="SHOP")
    assert response.result == CashierResult.OUT_OF_SCOPE
    assert response.active_campaign_kind == "TEST"

    redeemed = redeem_promocode(db_session, code="51000001", point_id="SHOP")
    assert redeemed.result == CashierResult.OUT_OF_SCOPE
    promo = db_session.scalar(select(Promocode).where(Promocode.promocode == "51000001"))
    assert promo is not None and promo.status == PromocodeStatus.ACTIVE


def test_cashier_serves_code_after_switch_to_live(db_session: Session) -> None:
    live = _campaign(db_session, code="live_wave2", kind=CampaignKind.LIVE, prefix="5")
    _promo(db_session, code="51000002", campaign=live, customer="778")
    set_active_kind(db_session, CampaignKind.LIVE)

    assert get_active_kind(db_session) == CampaignKind.LIVE
    response = check_promocode(db_session, code="51000002", point_id="SHOP")
    assert response.result == CashierResult.VALID
    assert response.campaign_kind == "LIVE"


def test_legacy_code_without_campaign_is_test_only(db_session: Session) -> None:
    _promo(db_session, code="19000001", campaign=None, customer="779")

    set_active_kind(db_session, CampaignKind.LIVE)
    assert check_promocode(db_session, code="19000001", point_id="S").result == (
        CashierResult.OUT_OF_SCOPE
    )

    set_active_kind(db_session, CampaignKind.TEST)
    assert check_promocode(db_session, code="19000001", point_id="S").result == CashierResult.VALID


def test_reconcile_skips_out_of_scope_and_closed_campaigns(db_session: Session) -> None:
    now = datetime.now(UTC)
    test_campaign = _campaign(db_session, code="tst", kind=CampaignKind.TEST, prefix="9")
    live_campaign = _campaign(db_session, code="lv", kind=CampaignKind.LIVE, prefix="5")
    closed_campaign = _campaign(db_session, code="lv_closed", kind=CampaignKind.LIVE, prefix="6")
    closed_campaign.status = CampaignStatus.CLOSED
    db_session.flush()

    _promo(db_session, code="91000001", campaign=test_campaign, customer="c1")
    _promo(db_session, code="51000003", campaign=live_campaign, customer="c2")
    _promo(db_session, code="61000001", campaign=closed_campaign, customer="c3")

    sales = [
        CoffeeSaleMatch(
            customer_erp_id=cid,
            sold_at=now + timedelta(minutes=5),
            group_id=11077,
            product_name="Coffee blend (250 g)",
            order_id=f"ord-{cid}",
            unit_price=45.0,
            quantity=2.0,
            net_weight_kg=0.25,
            line_kg=2.0,
        )
        for cid in ("c1", "c2", "c3")
    ]
    adapter = MockErpAdapter(sales=sales)

    set_active_kind(db_session, CampaignKind.LIVE)
    result = run_reconcile(
        db_session,
        settings=_settings(),
        adapter=adapter,
        now=now + timedelta(minutes=10),
    )

    assert result.auto_closed == ["51000003"]


def test_segment_import_uses_loyalty_card_as_promocode(db_session: Session) -> None:
    campaign = _campaign(db_session, code="seg", kind=CampaignKind.LIVE, prefix="5")
    rows = [
        SegmentRow(customer_erp_id=str(1000 + i), card=f"22000001{i:05d}") for i in range(20)
    ]

    result = import_segment(db_session, campaign=campaign, rows=rows, ttl_days=30)

    assert result.created_count == 20
    codes = [item.promocode for item in result.created]
    assert codes == [row.card for row in rows]
    assert len(set(codes)) == 20
    stored = db_session.scalar(
        select(Promocode).where(Promocode.customer_erp_id == "1000")
    )
    assert stored is not None
    assert stored.promocode == stored.customer_card == "2200000100000"

    # re-running must not issue a second code to the same customer
    again = import_segment(db_session, campaign=campaign, rows=rows, ttl_days=30)
    assert again.created_count == 0
    assert again.skipped_existing == 20


def test_segment_import_requires_card(db_session: Session) -> None:
    campaign = _campaign(db_session, code="seg_nocard", kind=CampaignKind.LIVE, prefix="5")
    result = import_segment(
        db_session,
        campaign=campaign,
        rows=[SegmentRow(customer_erp_id="2001")],
        ttl_days=30,
    )
    assert result.created_count == 0
    assert result.errors
    assert "missing loyalty card" in result.errors[0]


def test_segment_import_dry_run_writes_nothing(db_session: Session) -> None:
    campaign = _campaign(db_session, code="seg_dry", kind=CampaignKind.LIVE, prefix="5")
    rows = [SegmentRow(customer_erp_id="2001", card="2200000099999")]

    result = import_segment(db_session, campaign=campaign, rows=rows, ttl_days=30, dry_run=True)

    assert result.created_count == 1
    assert result.created[0].promocode == "2200000099999"
    stored = db_session.scalar(
        select(Promocode).where(Promocode.campaign_id == campaign.id)
    )
    assert stored is None


def test_rollback_keeps_touched_codes(db_session: Session) -> None:
    campaign = _campaign(db_session, code="seg_rb", kind=CampaignKind.LIVE, prefix="5")
    _promo(db_session, code="53000001", campaign=campaign, customer="3001")
    used = _promo(db_session, code="53000002", campaign=campaign, customer="3002")
    used.status = PromocodeStatus.USED
    used.redeemed_at = datetime.now(UTC)
    db_session.flush()

    deleted, kept = rollback_campaign_codes(db_session, campaign)

    assert (deleted, kept) == (1, 1)
    remaining = list(
        db_session.scalars(select(Promocode.promocode).where(Promocode.campaign_id == campaign.id))
    )
    assert remaining == ["53000002"]


def test_expires_at_follows_campaign_end(db_session: Session) -> None:
    campaign = _campaign(db_session, code="seg_end", kind=CampaignKind.LIVE, prefix="5")
    campaign.ends_at = datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)
    db_session.flush()

    result = import_segment(
        db_session,
        campaign=campaign,
        rows=[SegmentRow(customer_erp_id="4001", card="2200000040011")],
        ttl_days=30,
    )

    assert result.created[0].expires_at == campaign.ends_at
    assert result.created[0].promocode == "2200000040011"


def test_remap_promocode_to_card(db_session: Session) -> None:
    from app.services.promocode_remap import remap_campaign_promocodes_to_card

    campaign = _campaign(db_session, code="seg_remap", kind=CampaignKind.LIVE, prefix="5")
    promo = _promo(db_session, code="51000099", campaign=campaign, customer="5001")
    promo.customer_card = "2200000050011"
    db_session.flush()

    result = remap_campaign_promocodes_to_card(db_session, campaign)
    assert result.remapped_count == 1
    assert promo.promocode == "2200000050011"

    again = remap_campaign_promocodes_to_card(db_session, campaign)
    assert again.already_ok == 1
    assert again.remapped_count == 0
