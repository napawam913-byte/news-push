from __future__ import annotations

import json
import re
import csv
from dataclasses import asdict, dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


@dataclass(frozen=True)
class StockMatch:
    stock_code: str
    stock_name: str
    confidence: int
    reason: str


@dataclass(frozen=True)
class StockInfo:
    stock_code: str
    stock_name: str


class StockRecognizer:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.cache_path = data_dir / "a_stock_universe.json"
        self.alias_path = data_dir.parent / "config" / "stock_aliases.csv"
        self._stocks: list[StockInfo] | None = None
        self._aliases: list[tuple[str, StockInfo]] | None = None

    def recognize(self, title: str, summary: str = "") -> StockMatch | None:
        text = clean_html(f"{title}\n{summary}")

        alias_match = self._best_alias_match(text)
        if alias_match:
            alias, stock = alias_match
            return StockMatch(
                stock_code=stock.stock_code,
                stock_name=stock.stock_name,
                confidence=90,
                reason=f"命中别名：{alias}",
            )

        code_match = re.search(r"(?<!\d)([0368]\d{5})(?:\.(?:SH|SZ|BJ))?(?!\d)", text)
        if code_match:
            stock_code = code_match.group(1)
            stock = self._stock_by_code(stock_code)
            return StockMatch(
                stock_code=stock_code,
                stock_name=stock.stock_name if stock else "",
                confidence=95 if stock else 85,
                reason="命中6位股票代码",
            )

        best = self._best_name_match(text)
        if best:
            return StockMatch(
                stock_code=best.stock_code,
                stock_name=best.stock_name,
                confidence=80,
                reason="命中A股简称",
            )

        return None

    def stocks(self) -> list[StockInfo]:
        if self._stocks is None:
            self._stocks = self._load_stocks()
        return self._stocks

    def aliases(self) -> list[tuple[str, StockInfo]]:
        if self._aliases is None:
            self._aliases = self._load_aliases()
        return self._aliases

    def _stock_by_code(self, stock_code: str) -> StockInfo | None:
        for stock in self.stocks():
            if stock.stock_code == stock_code:
                return stock
        return None

    def _best_name_match(self, text: str) -> StockInfo | None:
        candidates: list[StockInfo] = []
        for stock in self.stocks():
            name = stock.stock_name
            if len(name) < 2:
                continue
            if name in text:
                candidates.append(stock)

        if not candidates:
            return None

        candidates.sort(key=lambda stock: len(stock.stock_name), reverse=True)
        return candidates[0]

    def _best_alias_match(self, text: str) -> tuple[str, StockInfo] | None:
        candidates: list[tuple[str, StockInfo]] = []
        for alias, stock in self.aliases():
            if alias and alias in text:
                candidates.append((alias, stock))
        if not candidates:
            return None
        candidates.sort(key=lambda item: len(item[0]), reverse=True)
        return candidates[0]

    def _load_aliases(self) -> list[tuple[str, StockInfo]]:
        if not self.alias_path.exists():
            return []

        aliases: list[tuple[str, StockInfo]] = []
        with self.alias_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                alias = str(row.get("alias", "")).strip()
                code = _normalize_stock_code(row.get("stock_code", ""))
                name = str(row.get("stock_name", "")).strip()
                if alias and code and name:
                    aliases.append((alias, StockInfo(stock_code=code, stock_name=name)))
        return aliases

    def _load_stocks(self) -> list[StockInfo]:
        cached = self._load_cache()
        if cached:
            return cached

        try:
            import akshare as ak
        except ImportError:
            print("[stock-warning] akshare is not installed, skip stock recognition")
            return []

        try:
            frame = ak.stock_info_a_code_name()
        except Exception as exc:
            print(f"[stock-warning] stock_info_a_code_name failed: {exc}")
            return []

        stocks: list[StockInfo] = []
        for _, row in frame.iterrows():
            code = _pick_text(row, ["code", "证券代码", "股票代码", "代码"])
            name = _pick_text(row, ["name", "证券简称", "股票简称", "名称"])
            code = _normalize_stock_code(code)
            if code and name:
                stocks.append(StockInfo(stock_code=code, stock_name=name))

        self._save_cache(stocks)
        return stocks

    def _load_cache(self) -> list[StockInfo]:
        if not self.cache_path.exists():
            return []
        try:
            rows = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        stocks: list[StockInfo] = []
        for row in rows:
            code = _normalize_stock_code(row.get("stock_code", ""))
            name = str(row.get("stock_name", "")).strip()
            if code and name:
                stocks.append(StockInfo(stock_code=code, stock_name=name))
        return stocks

    def _save_cache(self, stocks: list[StockInfo]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        rows = [asdict(stock) for stock in stocks]
        self.cache_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def clean_html(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(unescape(value or ""))
    text = parser.text()
    return re.sub(r"\s+", " ", text).strip()


def _pick_text(row, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""


def _normalize_stock_code(stock_code: str) -> str:
    text = str(stock_code).strip()
    if not text:
        return ""
    text = text.split(".")[0]
    if text.isdigit():
        return text.zfill(6)
    return text
