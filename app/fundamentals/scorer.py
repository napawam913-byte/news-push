from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class FundamentalMetrics:
    stock_code: str
    stock_name: str
    report_period: str
    announcement_date: str
    roe: float | None
    revenue_yoy: float | None
    net_profit_yoy: float | None
    operating_cash_flow_per_share: float | None
    gross_margin: float | None
    industry: str


@dataclass(frozen=True)
class FundamentalScore:
    metrics: FundamentalMetrics
    score: int
    is_quality: bool
    reasons: list[str]


class AkshareFundamentalScorer:
    def __init__(
        self,
        *,
        report_date: str = "",
        min_score: int = 70,
        lookback_periods: int = 8,
    ) -> None:
        self.report_date = report_date
        self.min_score = min_score
        self.lookback_periods = lookback_periods

    def score_stock_codes(self, stock_codes: set[str]) -> dict[str, FundamentalScore]:
        normalized_codes = {_normalize_stock_code(code) for code in stock_codes if code}
        normalized_codes.discard("")
        if not normalized_codes:
            return {}

        try:
            import akshare as ak
        except ImportError:
            print("[fundamental-warning] akshare is not installed, skip fundamental scoring")
            return {}

        scores: dict[str, FundamentalScore] = {}
        for report_period in self._candidate_report_dates():
            if normalized_codes.issubset(scores):
                break
            try:
                frame = ak.stock_yjbb_em(date=report_period)
            except Exception as exc:
                print(f"[fundamental-warning] stock_yjbb_em {report_period}: {exc}")
                continue
            if frame is None or getattr(frame, "empty", True):
                continue

            code_column = self._find_column(frame, ["股票代码", "代码"])
            if not code_column:
                continue

            missing_codes = normalized_codes - scores.keys()
            for _, row in frame.iterrows():
                stock_code = _normalize_stock_code(row.get(code_column, ""))
                if stock_code not in missing_codes:
                    continue

                metrics = self._row_to_metrics(row, stock_code, report_period)
                score, reasons = score_fundamentals(metrics)
                scores[stock_code] = FundamentalScore(
                    metrics=metrics,
                    score=score,
                    is_quality=score >= self.min_score,
                    reasons=reasons,
                )

        return scores

    def _candidate_report_dates(self) -> list[str]:
        if self.report_date:
            return [self.report_date]

        today = date.today()
        suffixes = ["1231", "0930", "0630", "0331"]
        candidates: list[str] = []
        for year in range(today.year, today.year - 4, -1):
            for suffix in suffixes:
                report_period = f"{year}{suffix}"
                if report_period <= today.strftime("%Y%m%d"):
                    candidates.append(report_period)
        return candidates[: self.lookback_periods]

    def _find_column(self, frame: Any, names: list[str]) -> str:
        for name in names:
            if name in frame.columns:
                return name
        return ""

    def _row_to_metrics(
        self,
        row: Any,
        stock_code: str,
        report_period: str,
    ) -> FundamentalMetrics:
        return FundamentalMetrics(
            stock_code=stock_code,
            stock_name=_pick_text(row, ["股票简称", "股票名称", "名称"]),
            report_period=report_period,
            announcement_date=_pick_text(row, ["最新公告日期", "公告日期"]),
            roe=_pick_float(row, ["净资产收益率"]),
            revenue_yoy=_pick_float(row, ["营业总收入-同比增长"]),
            net_profit_yoy=_pick_float(row, ["净利润-同比增长"]),
            operating_cash_flow_per_share=_pick_float(row, ["每股经营现金流量"]),
            gross_margin=_pick_float(row, ["销售毛利率"]),
            industry=_pick_text(row, ["所处行业", "行业"]),
        )


def score_fundamentals(metrics: FundamentalMetrics) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    score += _score_metric(
        metrics.roe,
        [(15, 30, "ROE>=15%"), (10, 24, "ROE>=10%"), (5, 12, "ROE>=5%")],
        miss_text="ROE缺失",
        fail_text="ROE偏低",
        fail_score=-10,
        reasons=reasons,
    )
    score += _score_metric(
        metrics.net_profit_yoy,
        [(30, 25, "净利润高增"), (10, 18, "净利润增长"), (0, 8, "净利润非负增长")],
        miss_text="净利润同比缺失",
        fail_text="净利润同比下滑",
        fail_score=-15,
        reasons=reasons,
    )
    score += _score_metric(
        metrics.revenue_yoy,
        [(20, 20, "营收高增"), (10, 14, "营收增长"), (0, 6, "营收非负增长")],
        miss_text="营收同比缺失",
        fail_text="营收同比下滑",
        fail_score=-10,
        reasons=reasons,
    )
    score += _score_metric(
        metrics.operating_cash_flow_per_share,
        [(0, 15, "经营现金流为正")],
        miss_text="经营现金流缺失",
        fail_text="经营现金流为负",
        fail_score=-10,
        reasons=reasons,
    )
    score += _score_metric(
        metrics.gross_margin,
        [(30, 10, "毛利率>=30%"), (20, 8, "毛利率>=20%"), (10, 4, "毛利率>=10%")],
        miss_text="毛利率缺失",
        fail_text="毛利率偏低",
        fail_score=0,
        reasons=reasons,
    )

    normalized_score = min(max(score, 0), 100)
    return normalized_score, reasons


def _score_metric(
    value: float | None,
    rules: list[tuple[float, int, str]],
    *,
    miss_text: str,
    fail_text: str,
    fail_score: int,
    reasons: list[str],
) -> int:
    if value is None:
        reasons.append(miss_text)
        return 0
    for threshold, points, reason in rules:
        if value >= threshold:
            reasons.append(reason)
            return points
    reasons.append(fail_text)
    return fail_score


def _pick_text(row: Any, names: list[str]) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return ""


def _pick_float(row: Any, names: list[str]) -> float | None:
    for name in names:
        if name not in row:
            continue
        value = row[name]
        try:
            if value is None:
                continue
            text = str(value).strip().replace("%", "").replace(",", "")
            if not text or text.lower() == "nan":
                continue
            return float(text)
        except (TypeError, ValueError):
            continue
    return None


def _normalize_stock_code(stock_code: Any) -> str:
    text = str(stock_code).strip()
    if not text:
        return ""
    text = text.split(".")[0]
    if text.isdigit():
        return text.zfill(6)
    return text
