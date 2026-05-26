from __future__ import annotations

import argparse
import time

from app.collectors.rss import RssCollector
from app.collectors.sample import SampleCollector
from app.collectors.akshare_stock_news import AkshareStockNewsCollector
from app.config import Settings, load_settings
from app.feishu.client import FeishuBitableClient, FeishuNotifier
from app.models import StoredMessage
from app.rules.classifier import RuleClassifier
from app.storage.local_store import LocalStore


def build_collectors(settings: Settings):
    collectors = []
    if settings.enable_sample_collector:
        collectors.append(SampleCollector())
    if settings.enable_rss_collector and settings.rss_urls:
        collectors.append(RssCollector(settings.rss_urls))
    if settings.enable_akshare_stock_news and settings.stock_codes:
        collectors.append(AkshareStockNewsCollector(settings.stock_codes))
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

    new_count = 0
    pushed_count = 0
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
                status="新增" if classification.is_positive else "忽略",
            )

            try:
                notifier.push(message)
                if message.pushed:
                    pushed_count += 1
            except Exception as exc:
                message.status = "推送失败"
                message.error_message = str(exc)

            try:
                bitable.create_record(message)
            except Exception as exc:
                message.error_message = f"{message.error_message}; bitable: {exc}".strip("; ")

            store.save(message)
            new_count += 1

    print(f"done new={new_count} pushed={pushed_count}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    settings = load_settings()
    if args.once:
        run_once(settings)
        return

    while True:
        run_once(settings)
        time.sleep(settings.interval_seconds)


if __name__ == "__main__":
    main()
