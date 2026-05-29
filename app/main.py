from __future__ import annotations

import argparse
import time

from app.collectors.rss import RssCollector
from app.collectors.sample import SampleCollector
from app.collectors.akshare_realtime_news import AkshareRealtimeNewsCollector
from app.collectors.akshare_stock_news import AkshareStockNewsCollector
from app.collectors.baidu_calendar import BaiduCalendarCollector
from app.collectors.caixin import CaixinNewsCollector
from app.collectors.cninfo_announcements import CninfoAnnouncementCollector
from app.collectors.cninfo_ratings import CninfoRatingCollector
from app.collectors.cninfo_relations import CninfoRelationCollector
from app.collectors.cctv_news import CctvNewsCollector
from app.collectors.eastmoney_notices import EastmoneyNoticeCollector
from app.collectors.eastmoney_research import EastmoneyResearchCollector
from app.collectors.stock_hot_rank import StockHotRankCollector
from app.config import Settings, load_settings
from app.feishu.client import FeishuBitableClient, FeishuNotifier
from app.fundamentals.scorer import AkshareFundamentalScorer, FundamentalScore
from app.models import Classification, StoredMessage, now_iso
from app.reports.hotspot_report import HotspotReportBuilder
from app.rules.classifier import RuleClassifier
from app.scheduler import (
    format_duration,
    is_active_now,
    next_interval_seconds,
    seconds_until_next_active_window,
)
from app.storage.local_store import LocalStore
from app.stocks.recognizer import StockRecognizer


def build_collectors(settings: Settings):
    collectors = []
    stock_recognizer = StockRecognizer(settings.data_dir)
    if settings.enable_sample_collector:
        collectors.append(SampleCollector())
    if settings.enable_rss_collector and settings.rss_urls:
        collectors.append(RssCollector(settings.rss_urls, stock_recognizer))
    if settings.enable_akshare_realtime_news_collector:
        collectors.append(
            AkshareRealtimeNewsCollector(
                settings.akshare_realtime_sources,
                stock_recognizer=stock_recognizer,
                limit_per_source=settings.akshare_realtime_limit_per_source,
            )
        )
    if settings.enable_akshare_stock_news and settings.stock_codes:
        collectors.append(AkshareStockNewsCollector(settings.stock_codes))
    if settings.enable_baidu_calendar_collector:
        collectors.append(
            BaiduCalendarCollector(
                lookback_days=settings.baidu_calendar_lookback_days,
                economic_min_importance=settings.baidu_economic_min_importance,
            )
        )
    if settings.enable_stock_hot_rank_collector:
        collectors.append(StockHotRankCollector(top_n=settings.stock_hot_rank_top_n))
    if settings.enable_cctv_news_collector:
        collectors.append(
            CctvNewsCollector(
                lookback_days=settings.cctv_news_lookback_days,
                stock_recognizer=stock_recognizer,
            )
        )
    if settings.enable_cninfo_collector:
        cninfo_stock_codes = settings.cninfo_stock_codes or settings.stock_codes
        if cninfo_stock_codes:
            collectors.append(
                CninfoAnnouncementCollector(
                    cninfo_stock_codes,
                    market=settings.cninfo_market,
                    categories=settings.cninfo_categories,
                    lookback_days=settings.cninfo_lookback_days,
                )
            )
    if settings.enable_cninfo_relation_collector:
        relation_stock_codes = settings.cninfo_stock_codes or settings.stock_codes
        if relation_stock_codes:
            collectors.append(
                CninfoRelationCollector(
                    relation_stock_codes,
                    market=settings.cninfo_market,
                    lookback_days=settings.cninfo_relation_lookback_days,
                )
            )
    if settings.enable_cninfo_rating_collector:
        collectors.append(
            CninfoRatingCollector(lookback_days=settings.cninfo_rating_lookback_days)
        )
    if settings.enable_eastmoney_notice_collector:
        collectors.append(
            EastmoneyNoticeCollector(
                categories=settings.eastmoney_notice_categories,
                lookback_days=settings.eastmoney_notice_lookback_days,
            )
        )
    if settings.enable_eastmoney_research_collector:
        research_stock_codes = settings.eastmoney_research_stock_codes or settings.stock_codes
        if research_stock_codes:
            collectors.append(
                EastmoneyResearchCollector(
                    research_stock_codes,
                    lookback_days=settings.eastmoney_research_lookback_days,
                )
            )
    if settings.enable_caixin_collector:
        collectors.append(CaixinNewsCollector(stock_recognizer))
    return collectors


def run_once(settings: Settings) -> None:
    store = LocalStore(settings.data_dir)
    classifier = RuleClassifier()
    notifier = FeishuNotifier(settings.feishu_webhook, dry_run=settings.dry_run)
    bitable = FeishuBitableClient(
        app_id=settings.feishu_app_id,
        app_secret=settings.feishu_app_secret,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
        dry_run=settings.dry_run,
    )

    collectors = build_collectors(settings)
    print(f"collectors={','.join(c.name for c in collectors) or 'none'} dry_run={settings.dry_run}")

    messages: list[StoredMessage] = []
    for collector in collectors:
        try:
            items = collector.collect()
        except Exception as exc:
            print(f"[collector-error] {collector.name}: {exc}")
            continue

        for item in items:
            message_id = item.message_id()
            if store.exists(message_id):
                continue

            classification = classifier.classify(item)
            message = StoredMessage(
                message_id=message_id,
                item=item,
                classification=classification,
                status=initial_status(item.stock_code, classification),
            )
            messages.append(message)

    fundamental_scores = build_fundamental_scores(settings, messages)
    pushed_count = push_messages(settings, notifier, messages, fundamental_scores)

    for message in messages:
        try:
            bitable.create_record(message)
        except Exception as exc:
            message.error_message = f"{message.error_message}; bitable: {exc}".strip("; ")

        store.save(message)

    print(f"done new={len(messages)} pushed={pushed_count}")


def push_messages(
    settings: Settings,
    notifier: FeishuNotifier,
    messages: list[StoredMessage],
    fundamental_scores: dict[str, FundamentalScore],
) -> int:
    if not messages:
        return 0

    if not settings.batch_push_enabled:
        pushed_count = 0
        for message in messages:
            if not should_include_in_report(message):
                continue
            try:
                notifier.push(message)
                if message.pushed:
                    pushed_count += 1
            except Exception as exc:
                message.status = "推送失败"
                message.error_message = str(exc)
        return pushed_count

    push_candidates = [
        message
        for message in messages
        if should_include_in_report(message) and notifier.should_push(message)
    ]
    if not push_candidates:
        return 0

    report_builder = HotspotReportBuilder(
        max_hotspots=settings.max_hotspots,
        max_recommendations=settings.max_recommendations,
    )
    reported_messages = report_builder.select_messages(push_candidates)
    report = report_builder.build(reported_messages, total_new=len(messages))
    if not report:
        return 0

    try:
        notifier.push_text(report)
    except Exception as exc:
        for message in reported_messages:
            message.status = "批次推送失败"
            message.error_message = str(exc)
        return 0

    push_time = now_iso()
    for message in reported_messages:
        message.pushed = True
        message.push_time = push_time
        message.status = "dry_run_批次已推送" if settings.dry_run else "批次已推送"
    return len(reported_messages)


def initial_status(stock_code: str, classification: Classification) -> str:
    if classification.tier == 3:
        return "忽略"
    if classification.sentiment in {"positive", "negative"} and not stock_code:
        return "未识别A股不推送"
    return "新增"


def should_include_in_report(message: StoredMessage) -> bool:
    cls = message.classification
    if cls.tier == 3:
        return False
    if cls.sentiment in {"positive", "negative"} and not message.item.stock_code:
        return False
    return True


def build_fundamental_scores(
    settings: Settings,
    messages: list[StoredMessage],
) -> dict[str, FundamentalScore]:
    if not settings.enable_fundamental_scoring:
        return {}

    stock_codes = {
        message.item.stock_code
        for message in messages
        if message.item.stock_code and message.classification.is_positive
    }
    if not stock_codes:
        return {}

    return AkshareFundamentalScorer(
        report_date=settings.fundamental_report_date,
        min_score=settings.min_fundamental_score,
    ).score_stock_codes(stock_codes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    settings = load_settings()
    if args.once:
        run_once(settings)
        return

    while True:
        if not is_active_now(settings):
            sleep_seconds = seconds_until_next_active_window(settings)
            print(f"outside active window, sleep {format_duration(sleep_seconds)}")
            time.sleep(sleep_seconds)
            continue

        run_once(settings)
        sleep_seconds = next_interval_seconds(settings)
        print(f"next run after {format_duration(sleep_seconds)}")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
