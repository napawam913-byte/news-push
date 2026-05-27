from __future__ import annotations

from datetime import date
import re

from app.models import NewsItem


class StockHotRankCollector:
    name = "stock_hot_rank"

    def __init__(self, *, top_n: int = 20) -> None:
        self.top_n = max(1, top_n)

    def collect(self) -> list[NewsItem]:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "akshare is not installed. Install it first: pip install akshare"
            ) from exc

        items: list[NewsItem] = []
        seen: set[str] = set()
        publish_time = date.today().isoformat()
        self._collect_em_rank(ak, publish_time, items, seen)
        self._collect_em_up(ak, publish_time, items, seen)
        self._collect_baidu_hot_search(ak, publish_time, items, seen)
        return items

    def _collect_em_rank(
        self,
        ak,
        publish_time: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.stock_hot_rank_em()
        except Exception as exc:
            print(f"[stock-hot-warning] eastmoney rank: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.head(self.top_n).iterrows():
            code = _normalize_code(_pick(row, ["代码", "股票代码"]))
            name = _pick(row, ["股票名称", "股票简称", "名称"])
            if not code or not name:
                continue
            rank = _pick(row, ["当前排名", "排名"])
            title = f"东方财富人气榜: {name}({code})"
            summary = (
                f"当前排名: {rank}; 最新价: {_pick(row, ['最新价'])}; "
                f"涨跌幅: {_pick(row, ['涨跌幅'])}%"
            )
            self._append(
                items,
                seen,
                NewsItem(
                    source="eastmoney/hot_rank",
                    source_type="hot_rank",
                    publish_time=publish_time,
                    stock_code=code,
                    stock_name=name,
                    title=title,
                    summary=summary,
                    raw_content=f"{title}\n{summary}",
                ),
            )

    def _collect_em_up(
        self,
        ak,
        publish_time: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.stock_hot_up_em()
        except Exception as exc:
            print(f"[stock-hot-warning] eastmoney hot up: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.head(self.top_n).iterrows():
            code = _normalize_code(_pick(row, ["代码", "股票代码"]))
            name = _pick(row, ["股票名称", "股票简称", "名称"])
            if not code or not name:
                continue
            title = f"东方财富飙升榜: {name}({code})"
            summary = (
                f"排名变动: {_pick(row, ['排名较昨日变动'])}; 当前排名: {_pick(row, ['当前排名'])}; "
                f"涨跌幅: {_pick(row, ['涨跌幅'])}%"
            )
            self._append(
                items,
                seen,
                NewsItem(
                    source="eastmoney/hot_up",
                    source_type="hot_rank",
                    publish_time=publish_time,
                    stock_code=code,
                    stock_name=name,
                    title=title,
                    summary=summary,
                    raw_content=f"{title}\n{summary}",
                ),
            )

    def _collect_baidu_hot_search(
        self,
        ak,
        publish_time: str,
        items: list[NewsItem],
        seen: set[str],
    ) -> None:
        try:
            frame = ak.stock_hot_search_baidu(
                symbol="A股",
                date=publish_time.replace("-", ""),
                time="今日",
            )
        except Exception as exc:
            print(f"[stock-hot-warning] baidu hot search: {exc}")
            return
        if frame is None or getattr(frame, "empty", True):
            return

        for _, row in frame.head(self.top_n).iterrows():
            code = _normalize_code(
                _pick(row, ["股票代码", "证券代码", "代码", "code", "marketCode"])
            )
            name = _pick(row, ["股票简称", "证券简称", "股票名称", "名称", "name"])
            if not code or not name:
                continue
            title = f"百度A股热搜: {name}({code})"
            summary = f"排名: {_pick(row, ['排名', 'rank'])}; 热度: {_pick(row, ['热度', 'heat'])}"
            self._append(
                items,
                seen,
                NewsItem(
                    source="baidu/hot_search",
                    source_type="hot_rank",
                    publish_time=publish_time,
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
        key = "|".join([item.source, item.stock_code, item.title, item.publish_time])
        if key not in seen:
            seen.add(key)
            items.append(item)


def _normalize_code(value: str) -> str:
    match = re.search(r"\d{6}", value or "")
    if not match:
        return ""
    code = match.group(0)
    return code if code.startswith(("0", "3", "6", "8", "4")) else ""


def _pick(row, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""
