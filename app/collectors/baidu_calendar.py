from __future__ import annotations

from datetime import date, timedelta
import re

from app.models import NewsItem


class BaiduCalendarCollector:
    name = "baidu_calendar"

    def __init__(
        self,
        *,
        lookback_days: int = 1,
        economic_min_importance: int = 2,
    ) -> None:
        self.lookback_days = max(1, lookback_days)
        self.economic_min_importance = max(0, economic_min_importance)

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
            date_iso = query_date.isoformat()
            self._collect_economic(ak, date_text, date_iso, items, seen)
            self._collect_report_times(ak, date_text, items, seen)
            self._collect_dividends(ak, date_text, items, seen)
            self._collect_suspend(ak, date_text, items, seen)
        return items

    def _collect_economic(
        self,
        ak,
        date_text: str,
        date_iso: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.news_economic_baidu(date=date_text)
        except Exception as exc:
            print(f"[baidu-calendar-warning] economic {date_text}: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.iterrows():
            importance = _to_int(_pick(row, ["重要性"]))
            if importance < self.economic_min_importance:
                continue
            event = _pick(row, ["事件"])
            region = _pick(row, ["地区"])
            if not event:
                continue
            publish_time = f"{date_iso} {_pick(row, ['时间'])}".strip()
            title = f"财经日历: {region}{event}"
            summary = (
                f"公布: {_pick(row, ['公布'])}; 预期: {_pick(row, ['预期'])}; "
                f"前值: {_pick(row, ['前值'])}; 重要性: {importance}"
            )
            self._append(
                items,
                seen,
                NewsItem(
                    source="baidu/economic_calendar",
                    source_type="calendar",
                    publish_time=publish_time,
                    title=title,
                    summary=summary,
                    raw_content=f"{title}\n{summary}",
                ),
            )

    def _collect_report_times(
        self,
        ak,
        date_text: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.news_report_time_baidu(date=date_text)
        except Exception as exc:
            print(f"[baidu-calendar-warning] report_time {date_text}: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.iterrows():
            code = _normalize_a_code(_pick(row, ["股票代码"]))
            if not code:
                continue
            name = _pick(row, ["股票简称"])
            report_type = _pick(row, ["财报类型"])
            publish_time = _pick(row, ["发布日期", "发布时间"]) or date_text
            title = f"{name}({code}) 财报披露: {report_type}".strip()
            self._append(
                items,
                seen,
                NewsItem(
                    source="baidu/report_calendar",
                    source_type="calendar",
                    publish_time=publish_time,
                    stock_code=code,
                    stock_name=name,
                    title=title,
                    summary=_pick(row, ["交易所"]),
                    raw_content=title,
                ),
            )

    def _collect_dividends(
        self,
        ak,
        date_text: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.news_trade_notify_dividend_baidu(date=date_text)
        except Exception as exc:
            print(f"[baidu-calendar-warning] dividend {date_text}: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.iterrows():
            code = _normalize_a_code(_pick(row, ["股票代码"]))
            if not code:
                continue
            name = _pick(row, ["股票简称"])
            dividend = _pick(row, ["分红"])
            title = f"{name}({code}) 分红除权: {dividend}".strip()
            summary = (
                f"除权日: {_pick(row, ['除权日'])}; 送股: {_pick(row, ['送股'])}; "
                f"转增: {_pick(row, ['转增'])}; 报告期: {_pick(row, ['报告期'])}"
            )
            self._append(
                items,
                seen,
                NewsItem(
                    source="baidu/dividend_calendar",
                    source_type="calendar",
                    publish_time=_pick(row, ["除权日", "报告期"]) or date_text,
                    stock_code=code,
                    stock_name=name,
                    title=title,
                    summary=summary,
                    raw_content=f"{title}\n{summary}",
                ),
            )

    def _collect_suspend(
        self,
        ak,
        date_text: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.news_trade_notify_suspend_baidu(date=date_text)
        except Exception as exc:
            print(f"[baidu-calendar-warning] suspend {date_text}: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.iterrows():
            code = _normalize_a_code(_pick(row, ["股票代码"]))
            if not code:
                continue
            name = _pick(row, ["股票简称"])
            reason = _pick(row, ["停牌事项说明"])
            title = f"{name}({code}) 停复牌: {reason}".strip()
            summary = f"停牌时间: {_pick(row, ['停牌时间'])}; 复牌时间: {_pick(row, ['复牌时间'])}"
            self._append(
                items,
                seen,
                NewsItem(
                    source="baidu/suspend_calendar",
                    source_type="calendar",
                    publish_time=_pick(row, ["公告日期", "停牌时间"]) or date_text,
                    stock_code=code,
                    stock_name=name,
                    title=title,
                    summary=summary,
                    raw_content=f"{title}\n{summary}",
                ),
            )

    def _append(
        self,
        items: list[NewsItem],
        seen: set[str],
        item: NewsItem,
    ) -> None:
        key = "|".join(
            [item.source, item.stock_code, item.title, item.publish_time, item.url]
        )
        if item.title and key not in seen:
            seen.add(key)
            items.append(item)


def _normalize_a_code(value: str) -> str:
    match = re.search(r"\d{6}", value or "")
    if not match:
        return ""
    code = match.group(0)
    return code if code.startswith(("0", "3", "6", "8", "4")) else ""


def _to_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _pick(row, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""
