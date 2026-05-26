from __future__ import annotations

from app.models import NewsItem


class AkshareStockNewsCollector:
    name = "akshare_stock_news"

    def __init__(self, stock_codes: list[str]) -> None:
        self.stock_codes = stock_codes

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        items: list[NewsItem] = []
        for code in self.stock_codes:
            frame = self._fetch_stock_news(ak, code)
            if frame is None:
                continue

            for _, row in frame.head(30).iterrows():
                title = self._pick(row, ["新闻标题", "标题", "title"])
                if not title:
                    continue

                items.append(
                    NewsItem(
                        source="akshare/eastmoney",
                        source_type="stock_news",
                        publish_time=self._pick(row, ["发布时间", "时间", "日期", "datetime"]),
                        stock_code=code,
                        stock_name=self._pick(row, ["股票简称", "证券简称", "名称"]),
                        title=title,
                        summary=self._pick(row, ["新闻内容", "摘要", "内容"]),
                        url=self._pick(row, ["新闻链接", "链接", "url"]),
                        raw_content=self._pick(row, ["新闻内容", "摘要", "内容"]),
                    )
                )

        return items

    def _fetch_stock_news(self, ak, code: str):
        if hasattr(ak, "stock_news_em"):
            try:
                return ak.stock_news_em(symbol=code)
            except TypeError:
                return ak.stock_news_em(stock=code)
        raise RuntimeError("akshare.stock_news_em is unavailable in this akshare version")

    def _pick(self, row, names: list[str]) -> str:
        for name in names:
            if name in row and row[name] is not None:
                return str(row[name])
        return ""
