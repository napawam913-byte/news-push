from __future__ import annotations

from datetime import date, timedelta

from app.models import NewsItem


class EastmoneyNoticeCollector:
    name = "eastmoney_notices"

    def __init__(
        self,
        *,
        categories: list[str] | None = None,
        lookback_days: int = 1,
    ) -> None:
        self.categories = categories or ["全部"]
        self.lookback_days = max(1, lookback_days)

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
            for category in self.categories:
                try:
                    frame = ak.stock_notice_report(symbol=category, date=date_text)
                except Exception as exc:
                    print(f"[eastmoney-notice-warning] {category} {date_text}: {exc}")
                    continue
                if frame is None or getattr(frame, "empty", True):
                    continue

                for _, row in frame.iterrows():
                    code = _pick(row, ["代码", "股票代码"])
                    title = _pick(row, ["公告标题", "标题"])
                    publish_time = _pick(row, ["公告日期", "公告时间"]) or str(query_date)
                    url = _pick(row, ["网址", "公告链接", "链接"])
                    key = "|".join([code, title, publish_time, url])
                    if not title or key in seen:
                        continue
                    seen.add(key)
                    items.append(
                        NewsItem(
                            source="eastmoney/notices",
                            source_type="announcement",
                            publish_time=publish_time,
                            stock_code=code,
                            stock_name=_pick(row, ["名称", "简称", "股票简称"]),
                            title=title,
                            summary=_pick(row, ["公告类型"]),
                            url=url,
                            raw_content=f"{title}\n{_pick(row, ['公告类型'])}",
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
