from __future__ import annotations

import requests
import time

from app.models import StoredMessage, now_iso


class FeishuNotifier:
    def __init__(self, webhook: str, dry_run: bool = True) -> None:
        self.webhook = webhook
        self.dry_run = dry_run

    def should_push(self, message: StoredMessage) -> bool:
        cls = message.classification
        return cls.tier in {1, 2}

    def push(self, message: StoredMessage) -> None:
        if not self.should_push(message):
            return

        text = self._format_text(message)
        self.push_text(text)
        message.pushed = True
        message.push_time = now_iso()
        message.status = "dry_run_已推送" if self.dry_run or not self.webhook else "已推送"

    def push_text(self, text: str) -> None:
        if self.dry_run or not self.webhook:
            print("[DRY-RUN] Feishu push:")
            print(text)
            return

        last_error: Exception | None = None
        for _ in range(3):
            try:
                response = requests.post(
                    self.webhook,
                    json={"msg_type": "text", "content": {"text": text}},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("code", 0) != 0:
                    raise RuntimeError(f"Feishu webhook error: {data}")
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(2)
        if last_error:
            raise last_error

    def _format_text(self, message: StoredMessage) -> str:
        item = message.item
        cls = message.classification
        stock = f"{item.stock_name} {item.stock_code}".strip() or "未识别"
        return (
            f"【A股利好监控】{cls.level}级 - {cls.positive_type}\n\n"
            f"股票：{stock}\n"
            f"来源：{item.source} / {item.source_type}\n"
            f"发布时间：{item.publish_time or '未知'}\n"
            f"标题：{item.title}\n\n"
            f"判断：{cls.reason}\n"
            f"置信度：{cls.confidence}%\n"
            f"链接：{item.url or '无'}"
        )


class FeishuBitableClient:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_token: str,
        table_id: str,
        dry_run: bool = True,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.dry_run = dry_run
        self._tenant_access_token = ""

    def enabled(self) -> bool:
        return bool(self.app_id and self.app_secret and self.app_token and self.table_id)

    def create_record(self, message: StoredMessage) -> None:
        fields = self._to_fields(message)
        if self.dry_run or not self.enabled():
            print("[DRY-RUN] Bitable record:")
            print(fields)
            return

        token = self._get_tenant_access_token()
        url = (
            "https://open.feishu.cn/open-apis/bitable/v1/apps/"
            f"{self.app_token}/tables/{self.table_id}/records"
        )
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={"fields": fields},
            timeout=10,
        )
        response.raise_for_status()

    def _get_tenant_access_token(self) -> str:
        if self._tenant_access_token:
            return self._tenant_access_token

        response = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("tenant_access_token", "")
        if not token:
            raise RuntimeError(f"Failed to get tenant_access_token: {data}")
        self._tenant_access_token = token
        return token

    def _to_fields(self, message: StoredMessage) -> dict:
        item = message.item
        cls = message.classification
        return {
            "message_id": message.message_id,
            "publish_time": item.publish_time,
            "fetch_time": item.fetch_time,
            "source": item.source,
            "source_type": item.source_type,
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "title": item.title,
            "summary": item.summary,
            "url": item.url,
            "positive_type": cls.positive_type,
            "level": cls.level,
            "confidence": cls.confidence,
            "hit_keywords": ",".join(cls.hit_keywords),
            "negative_keywords": ",".join(cls.negative_keywords),
            "llm_reason": cls.reason,
            "status": message.status,
            "pushed": message.pushed,
            "push_time": message.push_time,
        }
