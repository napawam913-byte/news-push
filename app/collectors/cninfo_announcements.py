from __future__ import annotations

from datetime import date, timedelta

from app.models import NewsItem


class CninfoAnnouncementCollector:
    name = "cninfo_announcements"

    def __init__(
        self,
        stock_codes: list[str],
        *,
        market: str = "沪深京",
        categories: list[str] | None = None,
        lookback_days: int = 7,
    ) -> None:
        self.stock_codes = stock_codes
        self.market = market
        self.categories = categories or [""]
        self.lookback_days = max(1, lookback_days)

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        end_date = date.today()
        start_date = end_date - timedelta(days=self.lookback_days)
        start_text = start_date.strftime("%Y%m%d")
        end_text = end_date.strftime("%Y%m%d")

        items: list[NewsItem] = []
        seen: set[str] = set()
        for stock_code in self.stock_codes:
            for category in self.categories:
                try:
                    frame = ak.stock_zh_a_disclosure_report_cninfo(
                        symbol=stock_code,
                        market=self.market,
                        category=category,
                        start_date=start_text,
                        end_date=end_text,
                    )
                except Exception as exc:
                    if _is_no_data_error(exc):
                        continue
                    print(
                        f"[cninfo-warning] {stock_code} category={category or '全部'}: {exc}"
                    )
                    continue

                if frame is None or getattr(frame, "empty", True):
                    continue

                for _, row in frame.iterrows():
                    code = _pick(row, ["代码", "股票代码"]) or stock_code
                    title = _pick(row, ["公告标题", "标题"])
                    publish_time = _pick(row, ["公告时间", "公告日期"])
                    url = _pick(row, ["公告链接", "链接"])
                    key = "|".join([code, title, publish_time, url])
                    if not title or key in seen:
                        continue
                    seen.add(key)
                    items.append(
                        NewsItem(
                            source="cninfo",
                            source_type="announcement",
                            publish_time=publish_time,
                            stock_code=code,
                            stock_name=_pick(row, ["简称", "股票简称"]),
                            title=title,
                            summary=title,
                            url=url,
                            raw_content=title,
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


def _is_no_data_error(exc: Exception) -> bool:
    text = str(exc)
    return "公告标题" in text and "columns" in text
