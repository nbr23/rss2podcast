from __future__ import annotations

import os
import tempfile
from pathlib import Path

import requests


class TTSClient:
    def __init__(self, endpoint: str, voice: str, timeout: int = 600):
        self.endpoint = endpoint.rstrip("/")
        self.voice = voice
        self.timeout = timeout

    def synthesize_to_file(self, text: str, dest: Path) -> None:
        payload = {
            "text": text,
            "voice": self.voice,
            "speed": 1.0,
            "outputFormat": "mp3",
        }
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".tts-", suffix=".mp3.tmp")
        os.close(fd)
        tmp_path = Path(tmp)
        try:
            with requests.post(
                f"{self.endpoint}/api/tts",
                json=payload,
                stream=False,
                timeout=self.timeout,
            ) as r:
                r.raise_for_status()
                with tmp_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            os.chmod(tmp_path, 0o644)
            os.replace(tmp_path, dest)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise
