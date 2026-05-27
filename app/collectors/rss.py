from __future__ import annotations

from app.models import NewsItem
from app.stocks.recognizer import StockRecognizer, clean_html

try:
    import feedparser
except ImportError:  # pragma: no cover
    feedparser = None

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


class RssCollector:
    name = "rss"

    def __init__(self, urls: list[str], stock_recognizer: StockRecognizer | None = None) -> None:
        self.urls = urls
        self.stock_recognizer = stock_recognizer

    def collect(self) -> list[NewsItem]:
        if feedparser is None:
            raise RuntimeError("feedparser is not installed")
        if requests is None:
            raise RuntimeError("requests is not installed")

        items: list[NewsItem] = []
        for url in self.urls:
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 news-push/1.0"},
                    timeout=(3, 5),
                )
            except Exception as exc:
                print(f"[rss-warning] {url}: {exc}")
                continue

            status = response.status_code
            if status >= 400:
                print(f"[rss-warning] {url}: http_status={status}")
                continue

            feed = feedparser.parse(response.content)
            if getattr(feed, "bozo", False):
                print(f"[rss-warning] {url}: {getattr(feed, 'bozo_exception', 'parse failed')}")
            source = feed.feed.get("title", "rss")
            for entry in feed.entries[:30]:
                title = clean_html(entry.get("title", ""))
                summary = clean_html(entry.get("summary", ""))
                stock_match = (
                    self.stock_recognizer.recognize(title, summary)
                    if self.stock_recognizer
                    else None
                )
                items.append(
                    NewsItem(
                        source=source,
                        source_type="news",
                        publish_time=entry.get("published", ""),
                        stock_code=stock_match.stock_code if stock_match else "",
                        stock_name=stock_match.stock_name if stock_match else "",
                        title=title,
                        summary=summary,
                        url=entry.get("link", ""),
                        raw_content=summary,
                    )
                )
        return items
