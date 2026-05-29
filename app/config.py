from __future__ import annotations

import os
import sys
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


def _find_env_file() -> Path | None:
    env_file = os.getenv("ENV_FILE", ".env")
    env_path = Path(env_file)
    if env_path.is_absolute() and env_path.exists():
        return env_path

    candidate_dirs: list[Path] = [Path.cwd()]
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidate_dirs.extend([exe_dir, exe_dir.parent])
    else:
        source_dir = Path(__file__).resolve().parent
        candidate_dirs.extend([source_dir, *source_dir.parents])

    seen: set[Path] = set()
    for directory in candidate_dirs:
        directory = directory.resolve()
        if directory in seen:
            continue
        seen.add(directory)
        candidate = directory / env_path
        if candidate.exists():
            return candidate
    return None


def _resolve_data_dir(base_dir: Path) -> Path:
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    if data_dir.is_absolute():
        return data_dir
    return base_dir / data_dir


@dataclass(frozen=True)
class Settings:
    dry_run: bool
    enable_sample_collector: bool
    enable_rss_collector: bool
    enable_akshare_stock_news: bool
    enable_cninfo_collector: bool
    enable_cninfo_relation_collector: bool
    enable_eastmoney_notice_collector: bool
    enable_eastmoney_research_collector: bool
    enable_caixin_collector: bool
    enable_akshare_realtime_news_collector: bool
    enable_baidu_calendar_collector: bool
    enable_stock_hot_rank_collector: bool
    enable_cctv_news_collector: bool
    enable_cninfo_rating_collector: bool
    rss_urls: list[str]
    stock_codes: list[str]
    cninfo_stock_codes: list[str]
    cninfo_market: str
    cninfo_categories: list[str]
    cninfo_lookback_days: int
    cninfo_relation_lookback_days: int
    eastmoney_notice_categories: list[str]
    eastmoney_notice_lookback_days: int
    eastmoney_research_stock_codes: list[str]
    eastmoney_research_lookback_days: int
    akshare_realtime_sources: list[str]
    akshare_realtime_limit_per_source: int
    baidu_calendar_lookback_days: int
    baidu_economic_min_importance: int
    stock_hot_rank_top_n: int
    cctv_news_lookback_days: int
    cninfo_rating_lookback_days: int
    interval_seconds: int
    interval_min_seconds: int
    interval_max_seconds: int
    workday_only: bool
    active_start_hour: int
    active_end_hour: int
    batch_push_enabled: bool
    max_hotspots: int
    max_recommendations: int
    enable_fundamental_scoring: bool
    fundamental_report_date: str
    min_fundamental_score: int
    quality_stock_codes: set[str]
    min_recommend_score: int
    data_dir: Path
    feishu_webhook: str
    feishu_app_id: str
    feishu_app_secret: str
    feishu_bitable_app_token: str
    feishu_bitable_table_id: str


def load_settings() -> Settings:
    env_path = _find_env_file()
    if load_dotenv:
        load_dotenv(dotenv_path=env_path or ".env", override=True, encoding="utf-8-sig")
    base_dir = env_path.parent if env_path else Path.cwd()

    interval_seconds = _int("INTERVAL_SECONDS", 7200)

    return Settings(
        dry_run=_bool("DRY_RUN", True),
        enable_sample_collector=_bool("ENABLE_SAMPLE_COLLECTOR", True),
        enable_rss_collector=_bool("ENABLE_RSS_COLLECTOR", False),
        enable_akshare_stock_news=_bool("ENABLE_AKSHARE_STOCK_NEWS", False),
        enable_cninfo_collector=_bool("ENABLE_CNINFO_COLLECTOR", False),
        enable_cninfo_relation_collector=_bool("ENABLE_CNINFO_RELATION_COLLECTOR", False),
        enable_eastmoney_notice_collector=_bool("ENABLE_EASTMONEY_NOTICE_COLLECTOR", False),
        enable_eastmoney_research_collector=_bool("ENABLE_EASTMONEY_RESEARCH_COLLECTOR", False),
        enable_caixin_collector=_bool("ENABLE_CAIXIN_COLLECTOR", False),
        enable_akshare_realtime_news_collector=_bool("ENABLE_AKSHARE_REALTIME_NEWS", False),
        enable_baidu_calendar_collector=_bool("ENABLE_BAIDU_CALENDAR_COLLECTOR", False),
        enable_stock_hot_rank_collector=_bool("ENABLE_STOCK_HOT_RANK_COLLECTOR", False),
        enable_cctv_news_collector=_bool("ENABLE_CCTV_NEWS_COLLECTOR", False),
        enable_cninfo_rating_collector=_bool("ENABLE_CNINFO_RATING_COLLECTOR", False),
        rss_urls=_csv("RSS_URLS"),
        stock_codes=_csv("STOCK_CODES"),
        cninfo_stock_codes=_csv("CNINFO_STOCK_CODES"),
        cninfo_market=os.getenv("CNINFO_MARKET", "沪深京"),
        cninfo_categories=_csv("CNINFO_CATEGORIES"),
        cninfo_lookback_days=_int("CNINFO_LOOKBACK_DAYS", 7),
        cninfo_relation_lookback_days=_int("CNINFO_RELATION_LOOKBACK_DAYS", 30),
        eastmoney_notice_categories=_csv("EASTMONEY_NOTICE_CATEGORIES"),
        eastmoney_notice_lookback_days=_int("EASTMONEY_NOTICE_LOOKBACK_DAYS", 1),
        eastmoney_research_stock_codes=_csv("EASTMONEY_RESEARCH_STOCK_CODES"),
        eastmoney_research_lookback_days=_int("EASTMONEY_RESEARCH_LOOKBACK_DAYS", 30),
        akshare_realtime_sources=_csv("AKSHARE_REALTIME_SOURCES"),
        akshare_realtime_limit_per_source=_int("AKSHARE_REALTIME_LIMIT_PER_SOURCE", 50),
        baidu_calendar_lookback_days=_int("BAIDU_CALENDAR_LOOKBACK_DAYS", 1),
        baidu_economic_min_importance=_int("BAIDU_ECONOMIC_MIN_IMPORTANCE", 2),
        stock_hot_rank_top_n=_int("STOCK_HOT_RANK_TOP_N", 20),
        cctv_news_lookback_days=_int("CCTV_NEWS_LOOKBACK_DAYS", 2),
        cninfo_rating_lookback_days=_int("CNINFO_RATING_LOOKBACK_DAYS", 3),
        interval_seconds=interval_seconds,
        interval_min_seconds=_int("INTERVAL_MIN_SECONDS", interval_seconds),
        interval_max_seconds=_int("INTERVAL_MAX_SECONDS", max(interval_seconds, 10800)),
        workday_only=_bool("WORKDAY_ONLY", True),
        active_start_hour=_int("ACTIVE_START_HOUR", 7),
        active_end_hour=_int("ACTIVE_END_HOUR", 24),
        batch_push_enabled=_bool("BATCH_PUSH_ENABLED", True),
        max_hotspots=_int("MAX_HOTSPOTS", 8),
        max_recommendations=_int("MAX_RECOMMENDATIONS", 5),
        enable_fundamental_scoring=_bool("ENABLE_FUNDAMENTAL_SCORING", True),
        fundamental_report_date=os.getenv("FUNDAMENTAL_REPORT_DATE", ""),
        min_fundamental_score=_int("MIN_FUNDAMENTAL_SCORE", 70),
        quality_stock_codes=set(_csv("QUALITY_STOCK_CODES")),
        min_recommend_score=_int("MIN_RECOMMEND_SCORE", 85),
        data_dir=_resolve_data_dir(base_dir),
        feishu_webhook=os.getenv("FEISHU_WEBHOOK", ""),
        feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
        feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
        feishu_bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", ""),
        feishu_bitable_table_id=os.getenv("FEISHU_BITABLE_TABLE_ID", ""),
    )
