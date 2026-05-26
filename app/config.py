from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def _csv(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    dry_run: bool
    enable_sample_collector: bool
    enable_rss_collector: bool
    enable_akshare_stock_news: bool
    rss_urls: list[str]
    stock_codes: list[str]
    interval_seconds: int
    data_dir: Path
    feishu_webhook: str
    feishu_app_id: str
    feishu_app_secret: str
    feishu_bitable_app_token: str
    feishu_bitable_table_id: str


def load_settings() -> Settings:
    if load_dotenv:
        load_dotenv(
            dotenv_path=os.getenv("ENV_FILE", ".env"),
            override=True,
            encoding="utf-8-sig",
        )

    return Settings(
        dry_run=_bool("DRY_RUN", True),
        enable_sample_collector=_bool("ENABLE_SAMPLE_COLLECTOR", True),
        enable_rss_collector=_bool("ENABLE_RSS_COLLECTOR", False),
        enable_akshare_stock_news=_bool("ENABLE_AKSHARE_STOCK_NEWS", False),
        rss_urls=_csv("RSS_URLS"),
        stock_codes=_csv("STOCK_CODES"),
        interval_seconds=_int("INTERVAL_SECONDS", 300),
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        feishu_webhook=os.getenv("FEISHU_WEBHOOK", ""),
        feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
        feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
        feishu_bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", ""),
        feishu_bitable_table_id=os.getenv("FEISHU_BITABLE_TABLE_ID", ""),
    )
