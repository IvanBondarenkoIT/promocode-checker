from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_timezone: str = Field(default="Asia/Tbilisi", alias="APP_TIMEZONE")
    app_secret_key: str = Field(default="change_me", alias="APP_SECRET_KEY")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5433/promocode_checker",
        alias="DATABASE_URL",
    )

    promocode_ttl_days: int = Field(default=30, alias="PROMOCODE_TTL_DAYS")
    fraud_match_window_hours: int = Field(default=2, alias="FRAUD_MATCH_WINDOW_HOURS")

    erp_access_mode: str = Field(default="proxy", alias="ERP_ACCESS_MODE")
    proxy_api_url: str = Field(default="", alias="PROXY_API_URL")
    proxy_api_token: str = Field(default="", alias="PROXY_API_TOKEN")
    proxy_api_timeout: int = Field(default=60, alias="PROXY_API_TIMEOUT")
    proxy_api_max_retries: int = Field(default=3, alias="PROXY_API_MAX_RETRIES")
    firebird_dsn: str = Field(default="", alias="FIREBIRD_DSN")
    firebird_user: str = Field(default="", alias="FIREBIRD_USER")
    firebird_password: str = Field(default="", alias="FIREBIRD_PASSWORD")

    coffee_beans_group_ids: str = Field(default="11077,16276,16279", alias="COFFEE_BEANS_GROUP_IDS")
    coffee_beans_param_id: int = Field(default=2, alias="COFFEE_BEANS_PARAM_ID")
    coffee_beans_param_value_id: int = Field(default=4, alias="COFFEE_BEANS_PARAM_VALUE_ID")
    erp_paid_statuses: str = Field(default="1,2,3,5", alias="ERP_PAID_STATUSES")

    default_point_id: str = Field(default="shop_01", alias="DEFAULT_POINT_ID")
    cashier_session_heartbeat_seconds: int = Field(
        default=60, alias="CASHIER_SESSION_HEARTBEAT_SECONDS"
    )

    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change_me_admin", alias="ADMIN_PASSWORD")
    viewer_username: str = Field(default="viewer", alias="VIEWER_USERNAME")
    viewer_password: str = Field(default="change_me_viewer", alias="VIEWER_PASSWORD")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_alert_chat_id: str = Field(default="", alias="TELEGRAM_ALERT_CHAT_ID")
    telegram_chat_ids: str = Field(default="", alias="TELEGRAM_CHAT_IDS")
    telegram_subscribe_keyword: str = Field(default="promo", alias="TELEGRAM_SUBSCRIBE_KEYWORD")
    telegram_notify_ok: int = Field(default=0, alias="TELEGRAM_NOTIFY_OK")
    telegram_dedup_window_seconds: int = Field(default=900, alias="TELEGRAM_DEDUP_WINDOW_SECONDS")
    telegram_disable_ssl_verify: int = Field(default=0, alias="TELEGRAM_DISABLE_SSL_VERIFY")
    telegram_day_start_hour: int = Field(default=10, alias="TELEGRAM_DAY_START_HOUR")
    telegram_day_start_minute: int = Field(default=0, alias="TELEGRAM_DAY_START_MINUTE")
    telegram_eod_hour: int = Field(default=22, alias="TELEGRAM_EOD_HOUR")
    telegram_eod_minute: int = Field(default=0, alias="TELEGRAM_EOD_MINUTE")
    telegram_digest_sales_row_limit: int = Field(
        default=5000, alias="TELEGRAM_DIGEST_SALES_ROW_LIMIT"
    )

    frontend_base_url: str = Field(default="http://localhost:8000", alias="FRONTEND_BASE_URL")
    static_dir: str = Field(default="", alias="STATIC_DIR")
    desktop_default_point_id: str = Field(default="shop_01", alias="DESKTOP_DEFAULT_POINT_ID")
    public_http_port: int = Field(default=8000, alias="PUBLIC_HTTP_PORT")

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
