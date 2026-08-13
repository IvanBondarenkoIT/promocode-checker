"""Single source of truth for Telegram alert topics and presets.

Routing must go through this module — do not add parallel event→topic maps.
"""

from __future__ import annotations

from collections.abc import Iterable

TOPIC_SCANS = "scans"
TOPIC_CLOSURES = "closures"
TOPIC_SALES = "sales"
TOPIC_FRAUD = "fraud"
TOPIC_DIGEST = "digest"
TOPIC_SYSTEM = "system"

ALL_TOPICS: tuple[str, ...] = (
    TOPIC_SCANS,
    TOPIC_CLOSURES,
    TOPIC_SALES,
    TOPIC_FRAUD,
    TOPIC_DIGEST,
    TOPIC_SYSTEM,
)

MANDATORY_TOPICS: frozenset[str] = frozenset({TOPIC_SYSTEM})

TOPIC_LABELS: dict[str, str] = {
    TOPIC_SCANS: "Сканы на кассе",
    TOPIC_CLOSURES: "Закрытия кодов",
    TOPIC_SALES: "Продажи кофе (ERP)",
    TOPIC_FRAUD: "Тревоги (антифрод)",
    TOPIC_DIGEST: "Сводки дня",
    TOPIC_SYSTEM: "Системные (обязательно)",
}

TOPIC_DESCRIPTIONS: dict[str, str] = {
    TOPIC_SCANS: "Каждый скан промокода: ACTIVE / USED / EXPIRED / NOT FOUND.",
    TOPIC_CLOSURES: "Ручное закрытие кассиром и автозакрытие по продаже.",
    TOPIC_SALES: "Продажа кофе клиента: условие выполнено или кг не хватает.",
    TOPIC_FRAUD: "Ручное закрытие без продажи кофе в окне антифрода.",
    TOPIC_DIGEST: "Старт дня (~10:00) и итог дня (~22:00).",
    TOPIC_SYSTEM: (
        "Сбои reconcile/ERP, ошибки сводки, смена TEST/LIVE, новые подписчики. "
        "Нельзя отключить."
    ),
}

EVENT_TOPIC: dict[str, str] = {
    "cashier_scan": TOPIC_SCANS,
    "cashier_manual_close": TOPIC_CLOSURES,
    "reconcile_auto_close": TOPIC_CLOSURES,
    "sale_observed": TOPIC_SALES,
    "fraud_warning": TOPIC_FRAUD,
    "day_start": TOPIC_DIGEST,
    "day_end": TOPIC_DIGEST,
    "job_crash": TOPIC_SYSTEM,
    "digest_error": TOPIC_SYSTEM,
    "scope_switched": TOPIC_SYSTEM,
    "subscriber_joined": TOPIC_SYSTEM,
}

ALERT_MODE_FULL = "full"
ALERT_MODE_DIGEST = "digest"
ALERT_MODE_CUSTOM = "custom"
ALERT_MODE_CRITICAL = "critical"
ALERT_MODE_SALES = "sales"

PRESET_TOPICS: dict[str, frozenset[str]] = {
    ALERT_MODE_FULL: frozenset(ALL_TOPICS),
    ALERT_MODE_DIGEST: frozenset({TOPIC_DIGEST, TOPIC_SYSTEM}),
    ALERT_MODE_CRITICAL: frozenset({TOPIC_FRAUD, TOPIC_SYSTEM}),
    ALERT_MODE_SALES: frozenset({TOPIC_SALES, TOPIC_SYSTEM}),
}

DEFAULT_TOPICS_CSV = ",".join(ALL_TOPICS)


def topic_for_event(event_type: str) -> str:
    """Map event_type to a topic; unknown events go to system (always delivered)."""
    return EVENT_TOPIC.get((event_type or "").strip(), TOPIC_SYSTEM)


def normalize_topics(raw: Iterable[str] | str | None) -> frozenset[str]:
    if raw is None:
        return frozenset(ALL_TOPICS)
    if isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    else:
        parts = [str(p).strip().lower() for p in raw if str(p).strip()]
    chosen = {p for p in parts if p in ALL_TOPICS}
    chosen |= set(MANDATORY_TOPICS)
    if not chosen:
        return frozenset(ALL_TOPICS)
    return frozenset(chosen)


def topics_to_csv(topics: Iterable[str]) -> str:
    chosen = normalize_topics(topics)
    return ",".join(t for t in ALL_TOPICS if t in chosen)


def topics_from_csv(raw: str | None) -> frozenset[str]:
    return normalize_topics(raw)


def preset_topics(preset: str) -> frozenset[str]:
    key = (preset or "").strip().lower()
    return PRESET_TOPICS.get(key, frozenset(ALL_TOPICS))


def infer_alert_mode(topics: Iterable[str]) -> str:
    chosen = normalize_topics(topics)
    for mode, expected in PRESET_TOPICS.items():
        if chosen == expected:
            return mode
    return ALERT_MODE_CUSTOM


def has_topic(topics_csv: str | None, topic: str) -> bool:
    return topic in topics_from_csv(topics_csv)


def toggle_topic(topics_csv: str | None, topic: str) -> str:
    """Toggle an optional topic; system always stays on."""
    topic = (topic or "").strip().lower()
    if topic not in ALL_TOPICS or topic in MANDATORY_TOPICS:
        return topics_to_csv(topics_from_csv(topics_csv))
    current = set(topics_from_csv(topics_csv))
    if topic in current:
        current.remove(topic)
    else:
        current.add(topic)
    return topics_to_csv(current)


def format_subscriptions_text(topics_csv: str | None) -> str:
    chosen = topics_from_csv(topics_csv)
    lines = ["Ваши подписки:", ""]
    for topic in ALL_TOPICS:
        mark = "✅" if topic in chosen else "⬜"
        label = TOPIC_LABELS[topic]
        desc = TOPIC_DESCRIPTIONS[topic]
        lines.append(f"{mark} {label}")
        lines.append(f"   {desc}")
        lines.append("")
    lines.append("Настроить: кнопка «Настроить» или /topics")
    return "\n".join(lines).rstrip()
