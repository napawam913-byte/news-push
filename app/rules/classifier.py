from __future__ import annotations

import re

from app.models import Classification, NewsItem

POSITIVE_RULES: dict[str, tuple[str, int]] = {
    "重大合同": ("重大合同", 35),
    "签订合同": ("重大合同", 30),
    "中标": ("中标", 30),
    "业绩预增": ("业绩增长", 40),
    "净利润增长": ("业绩增长", 35),
    "扭亏为盈": ("业绩增长", 35),
    "回购": ("回购", 30),
    "增持": ("增持", 25),
    "并购": ("并购重组", 35),
    "重组": ("并购重组", 40),
    "资产注入": ("并购重组", 40),
    "战略合作": ("战略合作", 20),
    "产品获批": ("产品获批", 30),
    "订单增长": ("订单增长", 25),
    "国产替代": ("主题催化", 15),
    "算力": ("主题催化", 15),
    "AI": ("主题催化", 15),
    "人工智能": ("主题催化", 15),
    "机器人": ("主题催化", 15),
    "低空经济": ("主题催化", 15),
    "半导体": ("主题催化", 15),
    "新能源": ("主题催化", 15),
}

NEGATIVE_WORDS = [
    "减持",
    "亏损",
    "立案",
    "处罚",
    "终止",
    "暂停",
    "退市",
    "跌停",
    "业绩下滑",
    "合同取消",
    "诉讼",
    "仲裁",
    "监管函",
    "问询函",
]


class RuleClassifier:
    def classify(self, item: NewsItem) -> Classification:
        text = f"{item.title}\n{item.summary}\n{item.raw_content}"
        hit_keywords: list[str] = []
        negative_keywords = [word for word in NEGATIVE_WORDS if word in text]
        type_scores: dict[str, int] = {}

        for keyword, (positive_type, score) in POSITIVE_RULES.items():
            if self._contains_keyword(text, keyword):
                hit_keywords.append(keyword)
                type_scores[positive_type] = type_scores.get(positive_type, 0) + score

        if not hit_keywords or negative_keywords:
            reason = "未命中利好关键词" if not hit_keywords else "命中负面关键词，暂不推送"
            return Classification(
                is_positive=False,
                level="忽略",
                positive_type="",
                confidence=20 if not hit_keywords else 35,
                hit_keywords=hit_keywords,
                negative_keywords=negative_keywords,
                reason=reason,
            )

        positive_type, score = max(type_scores.items(), key=lambda pair: pair[1])
        if item.source_type == "announcement":
            score += 15
        if item.stock_code:
            score += 5

        confidence = min(score + 35, 95)
        if confidence >= 85:
            level = "S"
        elif confidence >= 75:
            level = "A"
        elif confidence >= 60:
            level = "B"
        else:
            level = "C"

        return Classification(
            is_positive=True,
            level=level,
            positive_type=positive_type,
            confidence=confidence,
            hit_keywords=hit_keywords,
            negative_keywords=negative_keywords,
            reason=f"命中 {', '.join(hit_keywords)}，按规则判断为{positive_type}类消息。",
        )

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        if keyword == "AI":
            return re.search(r"(?<![A-Za-z])AI(?![A-Za-z])", text, re.IGNORECASE) is not None
        return keyword in text
