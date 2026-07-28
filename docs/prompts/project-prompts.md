# Project Prompts

Reusable prompts for Cursor agents working on promocode-checker.

## 0) Continue from handoff

```text
Продолжаем promocode-checker.
Прочитай AGENTS.md, docs/context-handoff.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/decisions.md и последние docs/reports/.
Не переспрашивай уже зафиксированные решения из docs/decisions.md.
Работай по stage-gate на КАЖДОМ этапе:
тесты → ревью → docs/reports/stage-XX → обновить handoff/plan/INDEX/prompts → commit+push → короткий доклад → следующий этап только после OK.
Сейчас делаем: <STAGE_NAME>.
Бери готовый текст этапа из docs/prompts/stage-prompts.md.
```

## 1) Architecture / design

```text
Спроектируй/уточни реализацию для promocode-checker с учетом:
- FastAPI + PostgreSQL checker DB
- cashier PWA с absolute autofocus и scanner Enter
- admin/viewer роли
- ERP reconcile через Proxy API primary + direct fallback
- Telegram alerts на изменения, fraud и падения
- local / railway-demo / server-prod
Не ломай уже закрытые этапы. Сверяйся с docs/plan/IMPLEMENTATION_PLAN.md и docs/decisions.md.
```

## 2) Stage implementation

```text
Реализуй только текущий этап: <STAGE_NAME>.
Ограничения:
- не расползаться на следующие этапы
- писать чистый код и минимально необходимые комментарии
- покрыть этап тестами
- прогнать проверки этапа
- обновить docs/reports/stage-XX-....md
- обновить AGENTS.md, docs/context-handoff.md, docs/plan/IMPLEMENTATION_PLAN.md, docs/INDEX.md, docs/prompts/stage-prompts.md
- в конце дать короткий доклад: сделано / тесты / упущения / вопросы до следующего этапа
- в конце: commit + push (feature/* → develop), без вопроса владельцу
STAGE-GATE шаблон и тексты этапов: docs/prompts/stage-prompts.md
```

## 3) Stage review

```text
Сделай ревью только что завершенного этапа:
1. что реализовано
2. какие тесты прошли и что они доказали
3. что могло быть упущено
4. риски
5. какие вопросы нужно уточнить до следующего этапа
Обнови docs/reports/ соответствующим stage report.
Убедись, что stage-gate отражён в docs/prompts/stage-prompts.md для следующих этапов.
Не начинай следующий этап без подтверждения.
```

## 4) Antifraud review

```text
Проверь антифрод-логику:
- manual close без ERP sale в окне FRAUD_MATCH_WINDOW_HOURS
- auto-close ACTIVE при найденной продаже кофе со скидкой
- audit trail admin overrides
- Telegram alerts без спама (dedup)
- whitelist coffee group_ids 11077,16276,16279
Найди дыры и предложи минимальные правки.
```

## 5) Cashier UX review

```text
Проверь cashier UI как kiosk для сканера:
- одно поле, только цифры, ровно 8
- autofocus возвращается после blur/click/submit/result
- Enter от сканера отправляет форму
- debounce lock 1.5s
- крупные статусы ACTIVE/USED/NOT_FOUND
- audio: success = 1 high beep; error = 2 low buzzes
- point_id из URL/settings
Найди все случаи, где кассиру придется кликать мышкой, и устрани их.
```

## 6) Admin UI review

```text
Проверь admin UI:
- login через env credentials
- admin vs viewer
- dashboard “что происходит сейчас”
- просмотр всех таблиц checker DB
- controlled edits + audit
- USED→ACTIVE разрешен только admin с reason
```

## 7) Deploy review

```text
Проверь деплой-контур:
- local compose
- railway-demo
- server-prod Docker on Windows Server / RDP
- healthchecks, restart policy, crash Telegram alerts
- ветки develop / railway-demo / main
Сверься с соседними проектами dimkava-big-book, prices-monitoring-scrappers, stock-safety-monitor.
```

## 8) Resume after workspace switch

```text
Я открыл D:\CursorProjects\promocode-checker в Cursor.
Подхвати контекст из AGENTS.md и docs/.
Кратко подтверди текущий статус этапов и предложи следующий конкретный шаг без лишних вопросов по уже принятым решениям.
```
