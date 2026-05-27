from __future__ import annotations

from app.models import NewsItem
from app.stocks.recognizer import StockRecognizer


class CaixinNewsCollector:
    name = "caixin"

    def __init__(self, stock_recognizer: StockRecognizer | None = None) -> None:
        self.stock_recognizer = stock_recognizer

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        try:
            frame = ak.stock_news_main_cx()
        except Exception as exc:
            print(f"[caixin-warning] {exc}")
            return []

        items: list[NewsItem] = []
        if frame is None or getattr(frame, "empty", True):
            return items

        for _, row in frame.iterrows():
            title = _pick(row, ["summary"])
            url = _pick(row, ["url"])
            tag = _pick(row, ["tag"])
            if not title:
                continue
            stock_match = (
                self.stock_recognizer.recognize(title, tag) if self.stock_recognizer else None
            )
            items.append(
                NewsItem(
                    source="caixin",
                    source_type="news",
                    stock_code=stock_match.stock_code if stock_match else "",
                    stock_name=stock_match.stock_name if stock_match else "",
                    title=title,
                    summary=tag,
                    url=url,
                    raw_content=f"{tag}\n{title}",
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
