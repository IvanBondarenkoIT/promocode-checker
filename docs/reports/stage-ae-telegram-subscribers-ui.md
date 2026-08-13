# Stage AE — Telegram subscriber join alert + list UI

Date: 2026-08-14  
Branch: `feature/telegram-subscribers-ui`

## Goal

Notify all active ops subscribers (topic `system`) when someone new joins the alert bot, and let any active subscriber see the subscriber list from Telegram UI.

## Done

1. **Join alert** — after `subscribe(...)=True` (keyword `promo` or preset that creates/reactivates), fan-out `event_type=subscriber_joined` → topic `system`. Joining `chat_id` is excluded via `send_alert(..., exclude_chat_ids=...)`. Repeat `promo` while already active does not alert.
2. **Profile columns** — migration `010_telegram_subscriber_profile`: nullable `username`, `display_name` on `telegram_subscribers`. Updated from `message.from` / callback `from` on inbound traffic.
3. **List UI** — button «Подписчики» + `/subscribers`; active subscribers only. Format: count + `chat_id · @user · mode · date`, truncated ~3500 chars.
4. Keyboard layout:
   ```
   [ Мои подписки ]  [ Настроить ]
   [ Проверить код ] [ Подписчики ]
   [ Итоги дня ]     [ Помощь ]
   ```

## Tests

- `tests/backend/test_telegram_bot.py` — join alert excludes self; repeat promo silent; list for active / stranger
- `tests/backend/test_telegram_topics.py` — `subscriber_joined` → `system`
- ruff + pytest (Postgres `:5433`)

## Docs

- `docs/runbooks/telegram-alerts.md`
- `docs/decisions.md`
- status files updated (AGENTS, handoff, INDEX, prompts, rules)

## Open / deploy check

After `update-prod.ps1`: subscribe from a second chat → first chat gets join alert; «Подписчики» shows both.
