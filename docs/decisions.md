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
9. **UI language: English only.** All user-facing text in cashier PWA, admin UI, and desktop wrapper must be English. No i18n / no second locale for MVP. Use `en-US` for dates and times in the UI.

## Promo / antifraud rules

1. Promocode format: **8–20 digits** (loyalty cards are typically 13). Field `promocode` stays separate from `customer_card`; segment import currently sets them equal.
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

Telegram auto-close delivery mode:

- **one summary message per reconcile run** (not one alert per closed code)
- fraud warnings and job crashes remain event alerts with dedup

Setup runbook: [`docs/runbooks/telegram-alerts.md`](runbooks/telegram-alerts.md).

### Customer barcode Telegram bot (locked 2026-08-04)

Sending Code 128 images **to customers** is **out of scope** for `promocode-checker`.

This repo provides:

- `GET /api/v1/cashier/barcode/{code}` — generate PNG on the fly
- Campaign CSV import + seed scripts

A separate marketing / CRM Telegram bot (other project) may call the barcode API or export PNGs.

### Ops alert bot (locked 2026-08-04; digests 2026-08-04)

- Bot `@dimkava_promo_alerts_bot` with **self-subscribe**: `/start` → keyword `promo` → `/stop`
- Modes: **`full`** (events + digests) · **`digest`** (day digests only); `/full` · `/digest`
- Errors/crashes always to all active subscribers
- Recipients = DB subscribers ∪ `TELEGRAM_ALERT_CHAT_ID` ∪ `TELEGRAM_CHAT_IDS` (seeds = full)
- Human Russian messages for scan, manual close, AUTO_CLOSE (with sale/price/prior scan), fraud
- Daily digests (Asia/Tbilisi): **10:00** day start + morning ERP coffee check; **22:00** EOD sales + checker event counts
- Calibration: `/demo` or `scripts/send_telegram_message_samples.py`
- Runbook: [`docs/runbooks/telegram-alerts.md`](runbooks/telegram-alerts.md)
- AUTO_CLOSE ops alerts are **per code** (human detail); not a single dry summary dump

## Stage 4 / Stage 5 gate (locked 2026-07-28)

Supervisor gate before Cashier PWA:

1. Stage 4 is accepted as **done for local/mock**. Live Granit SQL validation is a follow-up (`Stage 4.1`), not a Stage 5 blocker.
2. Concurrent redeem row-lock is **deferred until after Stage 5 PWA**.
3. Telegram reconcile auto-close uses **run summary**, not per-code spam.

Coffee sale match for reconcile remains: whitelist group sale in window is enough for now; a strict discount-column filter is a later ERP refinement after live SQL validation.

## Stage 5 / Stage 6 gate (locked 2026-07-28)

Supervisor closed Stage 5 as **PASS**. Answers before Stage 6:

1. **Admin UI packaging:** same Vite app as cashier, separate protected route `/admin` (and login page). Not a second standalone frontend app for MVP.
2. **Concurrent redeem lock:** do as **Stage 5.1** mini-fix **before** Stage 6 Admin UI. Use DB row lock / safe close so double redeem cannot double-close.
3. **Git:** Stage 5 commit is recommended after PASS, but agents commit/push **only when the user explicitly asks**. Push is optional unless user requests remote backup/CI.

Stage 5 accepted follow-ups (not Stage 5 blockers):

- Hardware scanner check on RDP before Stage 7
- Persisted cashier sessions table only if Admin needs it
- Static frontend from FastAPI in Stage 8


## Campaigns and data scope (locked 2026-08-06)

1. Every campaign has a `kind`: **`TEST`** (rehearsals) or **`LIVE`** (real customers), fixed at creation.
2. One global switch — `app_settings.active_campaign_kind` — decides what the cashier, reconcile and fraud checks serve. Admin-only, audited, announced in Telegram.
3. Promocodes without a campaign count as `TEST` and are never served in `LIVE`.
4. Segment / LIVE import sets **`promocode = loyalty card`** (CSV `customer_name` → `customer_card` and `promocode`). Demo/seed still uses random 8-digit codes with optional prefix (`9` tests, `1`–`4` legacy demos). Random generation with prefix remains available for non-segment waves.
5. One promocode per customer per campaign, enforced by a DB constraint. Global unique on `promocode` means the same card cannot be issued twice across campaigns.
6. `expires_at` follows `campaigns.ends_at` when set, otherwise `PROMOCODE_TTL_DAYS`.
7. Segment files and issued-code exports are PII: `data/input/` and `artifacts/` stay gitignored.
8. Existing random 8-digit segment codes: remap with `scripts/remap_promocode_to_card.py` (or rollback + re-import) after migration `006`.

Runbooks: [`campaign-scope.md`](runbooks/campaign-scope.md), [`campaign-import.md`](runbooks/campaign-import.md), [`preprod-calibration.md`](runbooks/preprod-calibration.md).

## Delivery targets

1. Local development first (verify before promote)
2. Production on Windows Server Docker where cashiers open the app over RDP
3. **General / acceptance test runs** happen on **server-prod** (not a separate cloud demo)
4. **Railway dropped** (2026-08-04) — no `railway-demo` environment

## Branch strategy

- `develop` — active development
- `main` — production server Docker
- `feature/*` — stage work

## Stage gate

Every stage ends with:

1. tests
2. review
3. short markdown report in `docs/reports/`
4. open questions clarified before next stage
5. **git commit + push** on `feature/*`, merge to `develop`, push (do not ask owner each time)

## Git / delivery workflow (locked 2026-07-28)

At the end of **every** stage or sub-stage (e.g. 5.1):

1. Run stage tests and ruff/lint as applicable
2. Write/update `docs/reports/stage-XX-....md`
3. Update AGENTS / handoff / plan / INDEX / prompts
4. Commit on `feature/*` branch with a clear message
5. Merge into `develop` and **push** `feature/*` and `develop` to origin

Agents must **not** re-ask «нужен ли commit/push?» — this is the default stage gate.
