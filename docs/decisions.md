# Locked Decisions

These decisions are already agreed and should not be re-litigated unless the user explicitly changes them.

## Product / UX

1. Cashier interface needs **no login**.
2. Cashier sessions still track:
   - `point_id` (from URL/query/config)
   - entry time / heartbeat / last activity
3. Admin interface is separate and protected by env credentials.
4. Admin roles:
   - `admin` — full edit rights
   - `viewer` — read-only
5. Admin may perform maximum corrections, including:
   - `USED -> ACTIVE`
   - TTL / expires_at changes
   - manual close / reopen
   - service field fixes
6. Every admin edit must store: actor, action, old values, new values, reason, timestamp.
7. Cashiers work over **RDP on the server**, so we need:
   - web/PWA
   - lightweight desktop wrapper (almost like an app, no browser friction)
8. Concurrent multi-user access is required.

## Promo / antifraud rules

1. Promocode format: **exactly 8 digits**.
2. Statuses: `ACTIVE`, `USED`.
3. TTL comes from env (`PROMOCODE_TTL_DAYS`).
4. Soft fraud matching window: default **2 hours** (`FRAUD_MATCH_WINDOW_HOURS`).
5. ERP sale evidence is the antifraud source of truth.
6. Manual close without ERP coffee sale within the window creates a fraud warning.
7. Auto-close ACTIVE codes when ERP finds matching discounted coffee sale.

## Coffee beans matching

Primary whitelist from `granit-clients-based-segmentation` config:

| group_id | label |
|----------|-------|
| 11077 | Coffee Blasecafe blend (250 g) |
| 16276 | Coffee Blasercafe singl origin (250г) |
| 16279 | Coffee Blasercafe blend (1kg) |

Fallback / future expansion:

- config/admin editable whitelist
- optional param match: `Продукция = Кофе(кг)` (`param_id=2`, value used in segmentation tooling)

## ERP access

1. Primary: Proxy API (`PROXY_API_URL`, `PROXY_API_TOKEN`)
2. Fallback: direct read-only Firebird/ERP connection
3. Local tests: mock ERP provider

## Notifications

Telegram alerts are mandatory for:

- successful reconcile changes (auto-closes found)
- fraud / warning cases
- application crash / worker failure

Env:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALERT_CHAT_ID`
- dedup window to avoid spam

## Delivery targets

1. Local development first
2. Railway as intermediate demo for managers
3. Production on Windows Server Docker where cashiers open the app over RDP

## Branch strategy

- `develop` — active development
- `railway-demo` — Railway showcase
- `main` — production server Docker
- `feature/*` — stage work

## Stage gate

Every stage ends with:

1. tests
2. review
3. short markdown report in `docs/reports/`
4. open questions clarified before next stage
