from __future__ import annotations

from datetime import date, timedelta

from app.models import NewsItem


class CninfoRatingCollector:
    name = "cninfo_ratings"

    def __init__(self, *, lookback_days: int = 3) -> None:
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
            try:
                frame = ak.stock_rank_forecast_cninfo(date=date_text)
            except Exception as exc:
                print(f"[cninfo-rating-warning] {date_text}: {exc}")
                continue
            if frame is None or getattr(frame, "empty", True):
                continue

            for _, row in frame.iterrows():
                code = _pick(row, ["证券代码"])
                name = _pick(row, ["证券简称"])
                rating = _pick(row, ["投资评级"])
                publish_time = _pick(row, ["发布日期"]) or query_date.isoformat()
                if not code or not name or not rating:
                    continue
                change = _pick(row, ["评级变化"])
                institution = _pick(row, ["研究机构简称"])
                title = f"{name}({code}) 投资评级: {rating}"
                if change and change != "未知":
                    title = f"{title}，评级变化: {change}"
                summary = (
                    f"机构: {institution}; 研究员: {_pick(row, ['研究员名称'])}; "
                    f"前次评级: {_pick(row, ['前一次投资评级'])}; "
                    f"目标价: {_pick(row, ['目标价格-下限'])}-{_pick(row, ['目标价格-上限'])}"
                )
                key = "|".join([code, title, publish_time, institution])
                if key in seen:
                    continue
                seen.add(key)
                items.append(
                    NewsItem(
                        source="cninfo/ratings",
                        source_type="research_rating",
                        publish_time=publish_time,
                        stock_code=code,
                        stock_name=name,
                        title=title,
                        summary=summary,
                        raw_content=f"{title}\n{summary}",
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
