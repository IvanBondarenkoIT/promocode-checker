"""Remap existing campaign promocodes to loyalty card numbers."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Campaign, FraudWarning, Promocode
from app.services.promocode_generator import is_valid_promocode, promocode_format_hint


@dataclass
class RemapResult:
    already_ok: int = 0
    remapped: list[tuple[str, str, str]] = field(default_factory=list)
    # (customer_erp_id, old_code, new_code)
    errors: list[str] = field(default_factory=list)

    @property
    def remapped_count(self) -> int:
        return len(self.remapped)


def remap_campaign_promocodes_to_card(
    db: Session,
    campaign: Campaign,
    *,
    dry_run: bool = False,
) -> RemapResult:
    """Set ``promocode = customer_card`` for every row in the campaign.

    Keeps ACTIVE/USED status and ``promocode_id`` audit links. Updates matching
    ``fraud_warnings.promocode_value`` when the old code matches.
    """
    result = RemapResult()
    rows = list(db.scalars(select(Promocode).where(Promocode.campaign_id == campaign.id)).all())
    reserved_targets: set[str] = set()

    for promo in rows:
        card = (promo.customer_card or "").strip()
        if not card:
            result.errors.append(
                f"customer {promo.customer_erp_id}: missing customer_card "
                f"(old promocode {promo.promocode})"
            )
            continue
        if not is_valid_promocode(card):
            result.errors.append(
                f"customer {promo.customer_erp_id}: invalid card '{card}' "
                f"(need {promocode_format_hint()})"
            )
            continue

        if promo.promocode == card:
            result.already_ok += 1
            reserved_targets.add(card)
            continue

        if card in reserved_targets:
            result.errors.append(
                f"customer {promo.customer_erp_id}: target card '{card}' collides in campaign"
            )
            continue

        other = db.scalar(
            select(Promocode).where(
                Promocode.promocode == card,
                Promocode.id != promo.id,
            )
        )
        if other is not None:
            result.errors.append(
                f"customer {promo.customer_erp_id}: target '{card}' already used "
                f"by customer {other.customer_erp_id}"
            )
            continue

        reserved_targets.add(card)
        old_code = promo.promocode
        result.remapped.append((promo.customer_erp_id, old_code, card))

        if dry_run:
            continue

        db.execute(
            update(FraudWarning)
            .where(FraudWarning.promocode_value == old_code)
            .values(promocode_value=card)
        )
        promo.promocode = card

    if not dry_run and result.remapped:
        db.flush()
    return result
