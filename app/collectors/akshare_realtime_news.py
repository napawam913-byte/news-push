from __future__ import annotations

import re
from collections.abc import Callable

from app.models import NewsItem
from app.stocks.recognizer import StockRecognizer


class AkshareRealtimeNewsCollector:
    name = "akshare_realtime_news"

    def __init__(
        self,
        sources: list[str] | None = None,
        *,
        stock_recognizer: StockRecognizer | None = None,
        limit_per_source: int = 50,
    ) -> None:
        self.sources = sources or ["cls", "eastmoney", "sina", "ths", "futu", "cjzc"]
        self.stock_recognizer = stock_recognizer
        self.limit_per_source = max(1, limit_per_source)

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        configs = _source_configs(ak)
        items: list[NewsItem] = []
        seen: set[str] = set()

        for source_key in self.sources:
            source_key = source_key.strip().lower()
            config = configs.get(source_key)
            if not config:
                print(f"[akshare-realtime-warning] unknown source: {source_key}")
                continue

            try:
                frame = config.fetch()
            except Exception as exc:
                print(f"[akshare-realtime-warning] {source_key}: {exc}")
                continue

            if frame is None or getattr(frame, "empty", True):
                continue

            for _, row in frame.head(self.limit_per_source).iterrows():
                title = _pick(row, config.title_fields)
                summary = _pick(row, config.summary_fields)
                if not title:
                    title = _title_from_content(summary)
                if not title:
                    continue

                publish_time = _publish_time(row, config)
                url = _pick(row, ["链接", "url", "URL"])
                key = "|".join([config.source, title, publish_time, url])
                if key in seen:
                    continue
                seen.add(key)

                stock_match = (
                    self.stock_recognizer.recognize(title, summary)
                    if self.stock_recognizer
                    else None
                )
                items.append(
                    NewsItem(
                        source=config.source,
                        source_type="news",
                        publish_time=publish_time,
                        stock_code=stock_match.stock_code if stock_match else "",
                        stock_name=stock_match.stock_name if stock_match else "",
                        title=title,
                        summary=summary,
                        url=url,
                        raw_content=f"{title}\n{summary}".strip(),
                    )
                )

        return items


class _SourceConfig:
    def __init__(
        self,
        *,
        source: str,
        fetch: Callable[[], object],
        title_fields: list[str],
        summary_fields: list[str],
        time_fields: list[str],
    ) -> None:
        self.source = source
        self.fetch = fetch
        self.title_fields = title_fields
        self.summary_fields = summary_fields
        self.time_fields = time_fields


def _source_configs(ak) -> dict[str, _SourceConfig]:
    return {
        "cls": _SourceConfig(
            source="akshare/cls",
            fetch=lambda: ak.stock_info_global_cls(symbol="重点"),
            title_fields=["标题"],
            summary_fields=["内容", "摘要"],
            time_fields=["发布时间", "发布日期"],
        ),
        "eastmoney": _SourceConfig(
            source="akshare/eastmoney_7x24",
            fetch=ak.stock_info_global_em,
            title_fields=["标题"],
            summary_fields=["摘要", "内容"],
            time_fields=["发布时间"],
        ),
        "sina": _SourceConfig(
            source="akshare/sina_7x24",
            fetch=ak.stock_info_global_sina,
            title_fields=["标题"],
            summary_fields=["内容"],
            time_fields=["时间", "发布时间"],
        ),
        "ths": _SourceConfig(
            source="akshare/ths_7x24",
            fetch=ak.stock_info_global_ths,
            title_fields=["标题"],
            summary_fields=["内容"],
            time_fields=["发布时间"],
        ),
        "futu": _SourceConfig(
            source="akshare/futu_flash",
            fetch=ak.stock_info_global_futu,
            title_fields=["标题"],
            summary_fields=["内容"],
            time_fields=["发布时间"],
        ),
        "cjzc": _SourceConfig(
            source="akshare/eastmoney_cjzc",
            fetch=ak.stock_info_cjzc_em,
            title_fields=["标题"],
            summary_fields=["摘要", "内容"],
            time_fields=["发布时间"],
        ),
    }


def _publish_time(row, config: _SourceConfig) -> str:
    publish_time = _pick(row, config.time_fields)
    if config.source == "akshare/cls":
        date_text = _pick(row, ["发布日期"])
        time_text = _pick(row, ["发布时间"])
        if date_text and time_text and re.fullmatch(r"\d{2}:\d{2}:\d{2}", time_text):
            return f"{date_text} {time_text}"
    return publish_time


def _title_from_content(content: str) -> str:
    content = content.strip()
    if not content:
        return ""
    match = re.match(r"^【([^】]{2,80})】", content)
    if match:
        return match.group(1).strip()
    return re.split(r"[。！？\n]", content, maxsplit=1)[0][:80].strip()


def _pick(row, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""
