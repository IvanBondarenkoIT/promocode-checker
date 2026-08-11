"""Net weight / line kg for coffee bean packages.

Formula aligned with granit-clients-based-segmentation:
``line_kg = quantity (STORZDTGDS.SOURCE, pieces) × GOODS.NW`` with name/group fallback.
"""

from __future__ import annotations

import re

# Fallback when GOODS.NW is missing and name has no weight token.
GROUP_NET_WEIGHT_KG: dict[int, float] = {
    11077: 0.25,  # blend 250 g
    16276: 0.25,  # single origin 250 g
    16279: 1.0,  # blend 1 kg
}

_NET_WEIGHT_PATTERNS: tuple[tuple[re.Pattern[str], float], ...] = (
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*kg\b", re.I), 1.0),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*кг\b", re.I), 1.0),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*g\b", re.I), 0.001),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*г\b", re.I), 0.001),
)


def infer_net_weight_kg(product_name: str | None) -> float | None:
    name = str(product_name or "")
    for pattern, unit_mult in _NET_WEIGHT_PATTERNS:
        match = pattern.search(name)
        if not match:
            continue
        raw = match.group(1).replace(",", ".")
        try:
            value = float(raw) * unit_mult
        except ValueError:
            continue
        if value > 0:
            return value
    return None


def resolve_net_weight_kg(
    *,
    product_name: str | None = None,
    stored_nw: float | None = None,
    group_id: int | None = None,
) -> float | None:
    if stored_nw is not None:
        try:
            value = float(stored_nw)
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            return value
    from_name = infer_net_weight_kg(product_name)
    if from_name is not None:
        return from_name
    if group_id is not None and group_id in GROUP_NET_WEIGHT_KG:
        return GROUP_NET_WEIGHT_KG[group_id]
    return None


def line_kg(
    quantity: float | int | None,
    *,
    product_name: str | None = None,
    stored_nw: float | None = None,
    group_id: int | None = None,
) -> float | None:
    """Return kg for one order line, or None when weight cannot be resolved."""
    try:
        qty = float(quantity or 0)
    except (TypeError, ValueError):
        qty = 0.0
    nw = resolve_net_weight_kg(
        product_name=product_name,
        stored_nw=stored_nw,
        group_id=group_id,
    )
    if nw is None:
        return None
    return qty * nw
