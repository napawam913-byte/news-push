from __future__ import annotations

from datetime import date, timedelta

from app.models import NewsItem
from app.stocks.recognizer import StockRecognizer


class CctvNewsCollector:
    name = "cctv_news"

    def __init__(
        self,
        *,
        lookback_days: int = 2,
        stock_recognizer: StockRecognizer | None = None,
    ) -> None:
        self.lookback_days = max(1, lookback_days)
        self.stock_recognizer = stock_recognizer

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        items: list[NewsItem] = []
        seen: set[str] = set()
        today = date.today()
        for day_offset in range(self.lookback_days):
            query_date = today - timedelta(days=day_offset)
            date_text = query_date.strftime("%Y%m%d")
            try:
                frame = ak.news_cctv(date=date_text)
            except Exception as exc:
                print(f"[cctv-news-warning] {date_text}: {exc}")
                continue
            if frame is None or getattr(frame, "empty", True):
                continue

            for _, row in frame.iterrows():
                title = _pick(row, ["title", "标题"])
                content = _pick(row, ["content", "内容"])
                publish_time = _pick(row, ["date", "日期"]) or query_date.isoformat()
                if not title:
                    title = content[:80].strip()
                if not title:
                    continue
                key = "|".join([title, publish_time])
                if key in seen:
                    continue
                seen.add(key)
                stock_match = (
                    self.stock_recognizer.recognize(title, content)
                    if self.stock_recognizer
                    else None
                )
                items.append(
                    NewsItem(
                        source="cctv/news",
                        source_type="policy_news",
                        publish_time=publish_time,
                        stock_code=stock_match.stock_code if stock_match else "",
                        stock_name=stock_match.stock_name if stock_match else "",
                        title=f"新闻联播: {title}",
                        summary=content[:300],
                        raw_content=content,
                    )
                )
        return items


def _pick(row, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""
