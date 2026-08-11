# Stage X — Monitor mode + 2 kg rule

Date: 2026-08-11  
Branch: `feature/monitor-mode-kg`

## Goal

Observe coffee sales for campaign customers, compute kg per order, notify Telegram,
and only auto-close when `PROMO_ENFORCEMENT_MODE=enforce` and order ≥ 2 kg.

## Changes

| Area | What |
|------|------|
| ERP SQL | `I.SOURCE AS QUANTITY`, `G.NW AS NET_WEIGHT_KG` |
| Weight | `line_kg = SOURCE × NW` (+ name/group fallback) |
| Evaluation | per `order_id` verdicts QUALIFIED / NOT_ENOUGH_KG / UNKNOWN_WEIGHT |
| Migration `007` | `sale_observations` unique `(customer_erp_id, order_id)` |
| Reconcile | observe + notify; close only in enforce |
| Env | `PROMO_ENFORCEMENT_MODE`, `PROMO_MIN_COFFEE_KG`, `RECONCILE_INTERVAL_SECONDS` |
| Admin | sale_observations table; dashboard enforcement badge |
| Docs | `runbooks/enforcement-modes.md` |

## Default today

`PROMO_ENFORCEMENT_MODE=monitor` — safe for LIVE scope with real customers.

## Tests

Unit: weight + evaluation. Integration: monitor no-close, enforce close, not-enough, dedupe, fraud unchanged.
