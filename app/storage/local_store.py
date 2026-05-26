from __future__ import annotations

import json
from pathlib import Path

from app.models import StoredMessage


class LocalStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seen_path = self.data_dir / "seen_ids.txt"
        self.messages_path = self.data_dir / "messages.jsonl"
        self.seen = self._load_seen()

    def _load_seen(self) -> set[str]:
        if not self.seen_path.exists():
            return set()
        return {
            line.strip()
            for line in self.seen_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    def exists(self, message_id: str) -> bool:
        return message_id in self.seen

    def save(self, message: StoredMessage) -> None:
        self.seen.add(message.message_id)
        with self.seen_path.open("a", encoding="utf-8") as file:
            file.write(message.message_id + "\n")
        with self.messages_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")

