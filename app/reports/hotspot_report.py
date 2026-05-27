from __future__ import annotations

from datetime import datetime

from app.models import StoredMessage


class HotspotReportBuilder:
    def __init__(
        self,
        *,
        max_hotspots: int,
        max_recommendations: int,
    ) -> None:
        self.max_hotspots = max_hotspots
        self.max_recommendations = max_recommendations

    def build(self, messages: list[StoredMessage], total_new: int) -> str:
        messages = self.select_messages(messages)
        if not messages:
            return ""

        tier_1 = [message for message in messages if message.classification.tier == 1]
        tier_2 = [message for message in messages if message.classification.tier == 2]
        now_text = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"【财经消息筛选】{now_text}",
            f"新增消息：{total_new} 条；筛选投送：{len(messages)} 条",
        ]

        if tier_1:
            lines.extend(["", "一级消息："])
            lines.extend(self._format_top_messages(tier_1))

        if tier_2:
            lines.extend(["", "二级消息："])
            lines.extend(self._format_top_messages(tier_2[: self.max_hotspots]))

        lines.extend(["", "提示：以上为规则筛选后的消息投送，不构成投资建议。"])
        return "\n".join(lines)

    def select_messages(self, messages: list[StoredMessage]) -> list[StoredMessage]:
        messages = sorted(
            messages,
            key=lambda message: (
                message.classification.tier,
                -message.classification.confidence,
                -_time_score(message.item.publish_time),
            ),
        )
        tier_1 = self._take_representative(messages, tier=1)
        tier_2 = self._take_representative(messages, tier=2)
        return tier_1 + tier_2

    def _take_representative(
        self,
        messages: list[StoredMessage],
        *,
        tier: int,
    ) -> list[StoredMessage]:
        selected: list[StoredMessage] = []
        seen_keys: set[tuple[str, ...]] = set()
        for message in messages:
            if message.classification.tier != tier:
                continue
            key = _dedupe_key(message)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            selected.append(message)
            if len(selected) >= self.max_hotspots:
                break
        return selected

    def _format_top_messages(self, messages: list[StoredMessage]) -> list[str]:
        lines: list[str] = []
        push_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        for index, message in enumerate(messages[: self.max_hotspots], start=1):
            item = message.item
            cls = message.classification
            stock = _format_stock(item.stock_name, item.stock_code)
            sentiment = _sentiment_label(cls.sentiment)
            lines.append(f"{index}. {stock}｜{sentiment}｜{cls.positive_type or '关注消息'}")
            lines.append(f"   来源：{item.source}")
            lines.append(f"   发布时间：{item.publish_time or '未知'}")
            lines.append(f"   投送时间：{push_time}")
            lines.append(f"   {item.title}")
            if item.url:
                lines.append(f"   {item.url}")
        return lines


def _format_stock(stock_name: str, stock_code: str) -> str:
    stock = f"{stock_name} {stock_code}".strip()
    return stock or "市场/行业热点"


def _sentiment_label(sentiment: str) -> str:
    if sentiment == "positive":
        return "利好"
    if sentiment == "negative":
        return "利空"
    return "中性"


def _time_score(value: str) -> float:
    value = (value or "").strip()
    if not value:
        return 0
    for fmt, length in (
        ("%Y-%m-%d %H:%M:%S", 19),
        ("%Y-%m-%d %H:%M", 16),
        ("%Y-%m-%d", 10),
        ("%Y%m%d", 8),
    ):
        try:
            return datetime.strptime(value[:length], fmt).timestamp()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0


def _dedupe_key(message: StoredMessage) -> tuple[str, ...]:
    item = message.item
    cls = message.classification
    if item.stock_code:
        return (
            item.stock_code,
            cls.sentiment,
            cls.positive_type,
        )
    return (
        "market",
        cls.sentiment,
        cls.positive_type,
        _compact_title(item.title),
    )


def _compact_title(title: str) -> str:
    return "".join((title or "").split())[:40]
