from __future__ import annotations

from datetime import date, datetime, timedelta

from app.models import NewsItem


class EastmoneyResearchCollector:
    name = "eastmoney_research"

    def __init__(self, stock_codes: list[str], *, lookback_days: int = 30) -> None:
        self.stock_codes = stock_codes
        self.lookback_days = max(1, lookback_days)

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        cutoff = date.today() - timedelta(days=self.lookback_days)
        items: list[NewsItem] = []
        seen: set[str] = set()
        for stock_code in self.stock_codes:
            try:
                frame = ak.stock_research_report_em(symbol=stock_code)
            except Exception as exc:
                print(f"[eastmoney-research-warning] {stock_code}: {exc}")
                continue
            if frame is None or getattr(frame, "empty", True):
                continue

            for _, row in frame.iterrows():
                publish_time = _pick(row, ["日期"])
                if publish_time and _parse_date(publish_time) < cutoff:
                    continue

                title = _pick(row, ["报告名称"])
                url = _pick(row, ["报告PDF链接"])
                key = "|".join([stock_code, title, publish_time, url])
                if not title or key in seen:
                    continue
                seen.add(key)
                rating = _pick(row, ["东财评级"])
                institution = _pick(row, ["机构"])
                items.append(
                    NewsItem(
                        source="eastmoney/research",
                        source_type="research",
                        publish_time=publish_time,
                        stock_code=_pick(row, ["股票代码"]) or stock_code,
                        stock_name=_pick(row, ["股票简称"]),
                        title=title,
                        summary=f"{institution} {rating}".strip(),
                        url=url,
                        raw_content=f"{title}\n{institution}\n{rating}",
                    )
                )
        return items


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return date.min


def _pick(row, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""
