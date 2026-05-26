from __future__ import annotations

from app.models import NewsItem

try:
    import feedparser
except ImportError:  # pragma: no cover
    feedparser = None


class RssCollector:
    name = "rss"

    def __init__(self, urls: list[str]) -> None:
        self.urls = urls

    def collect(self) -> list[NewsItem]:
        if feedparser is None:
            raise RuntimeError("feedparser is not installed")

        items: list[NewsItem] = []
        for url in self.urls:
            feed = feedparser.parse(url)
            if getattr(feed, "bozo", False):
                print(f"[rss-warning] {url}: {getattr(feed, 'bozo_exception', 'parse failed')}")
            status = getattr(feed, "status", None)
            if status and status >= 400:
                print(f"[rss-warning] {url}: http_status={status}")
            source = feed.feed.get("title", "rss")
            for entry in feed.entries[:30]:
                items.append(
                    NewsItem(
                        source=source,
                        source_type="news",
                        publish_time=entry.get("published", ""),
                        title=entry.get("title", ""),
                        summary=entry.get("summary", ""),
                        url=entry.get("link", ""),
                        raw_content=entry.get("summary", ""),
                    )
                )
        return items
