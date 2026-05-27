from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class NewsItem:
    source: str
    source_type: str
    title: str
    url: str = ""
    publish_time: str = ""
    stock_code: str = ""
    stock_name: str = ""
    summary: str = ""
    raw_content: str = ""
    fetch_time: str = field(default_factory=now_iso)

    def message_id(self) -> str:
        raw = "|".join(
            [
                self.source,
                self.source_type,
                self.title,
                self.stock_code,
                self.publish_time,
                self.url,
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class Classification:
    is_positive: bool
    level: str
    positive_type: str
    confidence: int
    hit_keywords: list[str]
    negative_keywords: list[str]
    reason: str
    sentiment: str = "neutral"
    tier: int = 3


@dataclass
class StoredMessage:
    message_id: str
    item: NewsItem
    classification: Classification
    pushed: bool = False
    push_time: str = ""
    status: str = "新增"
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "item": asdict(self.item),
            "classification": asdict(self.classification),
            "pushed": self.pushed,
            "push_time": self.push_time,
            "status": self.status,
            "error_message": self.error_message,
        }

