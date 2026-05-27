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
    "分红": ("分红派息", 25),
    "派息": ("分红派息", 25),
    "现金分红": ("分红派息", 30),
    "除权": ("分红派息", 15),
    "解除质押": ("风险缓释", 25),
    "涨价": ("行业景气", 20),
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
    "停牌",
    "风险警示",
    "跌停",
    "业绩下滑",
    "业绩预减",
    "净利润下降",
    "评级下调",
    "取消分红",
    "合同取消",
    "诉讼",
    "仲裁",
    "监管函",
    "问询函",
]

NEUTRAL_RULES: dict[str, tuple[str, int]] = {
    "调研": ("机构调研", 15),
    "互动平台": ("互动问答", 15),
    "财经日历": ("财经日历", 20),
    "财报披露": ("财报披露", 20),
    "投资评级": ("机构观点", 20),
    "首次评级": ("机构观点", 15),
    "评级变化": ("机构观点", 15),
    "人气榜": ("市场热度", 20),
    "热搜": ("市场热度", 20),
    "飙升榜": ("市场热度", 20),
    "关注度": ("市场热度", 15),
    "新闻联播": ("政策动态", 15),
    "财经早餐": ("财经早报", 15),
    "会议": ("会议动态", 10),
    "政策": ("政策动态", 15),
    "规划": ("政策动态", 15),
    "跨境支付": ("金融基础设施", 20),
    "Swift": ("金融基础设施", 20),
    "行业": ("行业动态", 10),
    "景气": ("行业动态", 15),
    "涨幅": ("市场异动", 10),
    "主力资金": ("资金流向", 10),
    "机构买入": ("机构观点", 15),
    "买入": ("机构观点", 15),
    "强烈推荐": ("机构观点", 15),
    "研报": ("机构观点", 15),
    "评级": ("机构观点", 10),
    "调高": ("机构观点", 10),
}


class RuleClassifier:
    def classify(self, item: NewsItem) -> Classification:
        text = f"{item.title}\n{item.summary}\n{item.raw_content}"
        hit_keywords: list[str] = []
        negative_keywords = [word for word in NEGATIVE_WORDS if word in text]
        type_scores: dict[str, int] = {}
        neutral_hits: list[str] = []
        neutral_scores: dict[str, int] = {}

        for keyword, (positive_type, score) in POSITIVE_RULES.items():
            if self._contains_keyword(text, keyword):
                hit_keywords.append(keyword)
                type_scores[positive_type] = type_scores.get(positive_type, 0) + score

        for keyword, (neutral_type, score) in NEUTRAL_RULES.items():
            if self._contains_keyword(text, keyword):
                neutral_hits.append(keyword)
                neutral_scores[neutral_type] = neutral_scores.get(neutral_type, 0) + score

        if negative_keywords:
            confidence = min(45 + 10 * len(negative_keywords), 95)
            tier = 1 if confidence >= 75 and item.stock_code else 2
            return Classification(
                is_positive=False,
                level=_level(confidence),
                positive_type="利空",
                confidence=confidence,
                hit_keywords=hit_keywords,
                negative_keywords=negative_keywords,
                reason=f"命中负面关键词：{', '.join(negative_keywords)}。",
                sentiment="negative",
                tier=tier,
            )

        if not hit_keywords:
            if neutral_hits:
                neutral_type, score = max(neutral_scores.items(), key=lambda pair: pair[1])
                confidence = min(score + 35 + (5 if item.stock_code else 0), 75)
                tier = 2 if confidence >= 50 else 3
                return Classification(
                    is_positive=False,
                    level=_level(confidence),
                    positive_type=neutral_type,
                    confidence=confidence,
                    hit_keywords=neutral_hits,
                    negative_keywords=[],
                    reason=f"命中中性关注关键词：{', '.join(neutral_hits)}。",
                    sentiment="neutral",
                    tier=tier,
                )

            return Classification(
                is_positive=False,
                level="忽略",
                positive_type="",
                confidence=20,
                hit_keywords=[],
                negative_keywords=[],
                reason="未命中关注关键词",
                sentiment="neutral",
                tier=3,
            )

        positive_type, score = max(type_scores.items(), key=lambda pair: pair[1])
        if item.source_type == "announcement":
            score += 15
        if item.stock_code:
            score += 5

        confidence = min(score + 35, 95)
        level = _level(confidence)
        tier = 1 if confidence >= 75 and item.stock_code else 2

        return Classification(
            is_positive=True,
            level=level,
            positive_type=positive_type,
            confidence=confidence,
            hit_keywords=hit_keywords,
            negative_keywords=negative_keywords,
            reason=f"命中 {', '.join(hit_keywords)}，按规则判断为{positive_type}类消息。",
            sentiment="positive",
            tier=tier,
        )

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        if keyword == "AI":
            return re.search(r"(?<![A-Za-z])AI(?![A-Za-z])", text, re.IGNORECASE) is not None
        return keyword in text


def _level(confidence: int) -> str:
    if confidence >= 85:
        return "S"
    if confidence >= 75:
        return "A"
    if confidence >= 60:
        return "B"
    return "C"
