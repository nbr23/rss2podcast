from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class State:
    feed_url: str
    path: Path
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path, feed_url: str) -> "State":
        if path.is_file():
            data = json.loads(path.read_text())
            return cls(feed_url=data.get("feed_url", feed_url), path=path, entries=data.get("entries", {}))
        return cls(feed_url=feed_url, path=path)

    def has(self, guid: str) -> bool:
        return guid in self.entries

    def add(self, guid: str, record: dict[str, Any]) -> None:
        self.entries[guid] = record
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".state-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump({"feed_url": self.feed_url, "entries": self.entries}, f, indent=2, sort_keys=True)
            os.replace(tmp, self.path)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
