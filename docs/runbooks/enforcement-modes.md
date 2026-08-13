# Enforcement modes: monitor vs enforce

Controls whether a qualifying coffee sale **automatically closes** a promocode.
Separate from campaign scope (`TEST` / `LIVE`).

| Env | Meaning |
|-----|---------|
| `PROMO_ENFORCEMENT_MODE=monitor` | Find sales, store `sale_observations`, Telegram alert. **Never** auto-close. |
| `PROMO_ENFORCEMENT_MODE=enforce` | Same, plus `AUTO_CLOSE` when order ≥ `PROMO_MIN_COFFEE_KG`. |

Threshold: **2 kg coffee beans in one ERP order** (`PROMO_MIN_COFFEE_KG=2.0`).

```text
line_kg = STORZDTGDS.SOURCE   # already kg; do not multiply by GOODS.NW
order_kg = sum(line_kg) for the same order_id
```

Whitelist groups: `COFFEE_BEANS_GROUP_IDS=11077,16276,16279`.

## Telegram verdicts

| Verdict | Message idea |
|---------|----------------|
| `QUALIFIED` | «Акция сработала»; in monitor: «Промокод НЕ закрыт — режим наблюдения» |
| `NOT_ENOUGH_KG` | «условия не хватает» + купленные кг |
| `UNKNOWN_WEIGHT` | вес не распознан |

One alert per `(customer_erp_id, order_id)` thanks to unique constraint on `sale_observations`.

## Manual close still works

Cashier can close via GUI; admin can reopen `USED → ACTIVE` with reason.
Fraud check for manual close without coffee sale stays on in both modes.

## Switch to enforce

1. Confirm monitor alerts look right for several days.
2. Set `PROMO_ENFORCEMENT_MODE=enforce` in `infra/.env.prod`.
3. Rebuild / recreate reconcile container (`desktop\update-prod.ps1` or compose up).
4. Buy ≥2 kg on a shop card → expect `USED` + auto-close Telegram.

## Server monitor rehearsal

```powershell
# in infra/.env.prod
PROMO_ENFORCEMENT_MODE=monitor
PROMO_MIN_COFFEE_KG=2.0
RECONCILE_INTERVAL_SECONDS=900

cd C:\Projects\promocode-checker\desktop
.\update-prod.ps1
```

Admin → Dashboard shows **Enforcement: Monitor**. Table `sale_observations` lists detected orders.
