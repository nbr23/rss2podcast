from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from mutagen.mp3 import MP3

from .config import AppConfig, FeedConfig, slugify
from .extract import compose_speech
from .feed import fetch
from .publish import write_feed
from .state import State
from .tts import TTSClient

log = logging.getLogger(__name__)


def _mp3_duration(path: Path) -> int | None:
    try:
        return int(MP3(str(path)).info.length)
    except Exception as e:
        log.warning("could not read duration of %s: %s", path, e)
        return None


def process_feed(app: AppConfig, feed_cfg: FeedConfig) -> None:
    slug = slugify(feed_cfg.name)
    feed_dir = app.output_dir / slug
    feed_dir.mkdir(parents=True, exist_ok=True)
    state = State.load(feed_dir / "state.json", feed_cfg.url)

    log.info("[%s] fetching %s", feed_cfg.name, feed_cfg.url)
    entries = fetch(feed_cfg.url)
    entries.sort(key=lambda e: e.pub_date, reverse=True)
    limit = feed_cfg.limit if feed_cfg.limit is not None else app.limit
    if limit is not None:
        entries = entries[:limit]
    log.info("[%s] %d entries in feed, %d already in state", feed_cfg.name, len(entries), len(state.entries))

    tts = TTSClient(app.tts_endpoint, feed_cfg.voice)

    new_count = 0
    for entry in entries:
        if state.has(entry.guid):
            continue
        log.info("[%s] processing: %s", feed_cfg.name, entry.title)
        text, body = compose_speech(
            entry,
            fetch_full=not app.no_fetch,
            favor_recall=feed_cfg.favor_recall,
            favor_precision=feed_cfg.favor_precision,
            include_comments=feed_cfg.include_comments,
            include_tables=feed_cfg.include_tables,
            deduplicate=feed_cfg.deduplicate,
            fast_extraction=feed_cfg.fast_extraction,
            prune_xpath=feed_cfg.prune_xpath,
        )
        if not text.strip():
            log.warning("[%s] empty text for %s, skipping", feed_cfg.name, entry.guid)
            continue

        date_prefix = entry.pub_date.strftime("%Y-%m-%d")
        mp3_filename = f"{date_prefix}-{entry.guid[:12]}.mp3"
        mp3_path = feed_dir / mp3_filename

        try:
            tts.synthesize_to_file(text, mp3_path)
        except Exception as e:
            log.error("[%s] TTS failed for %s: %s", feed_cfg.name, entry.title, e)
            continue

        record = {
            "title": entry.title,
            "link": entry.link,
            "pub_date": entry.pub_date.isoformat(),
            "description": entry.summary_html or "",
            "mp3_filename": mp3_filename,
            "filesize": mp3_path.stat().st_size,
            "duration_seconds": _mp3_duration(mp3_path),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "text_source": body.source,
        }
        if app.save_text:
            record["raw_text"] = body.raw
            record["tts_text"] = text
        state.add(entry.guid, record)
        new_count += 1

    log.info("[%s] processed %d new entries", feed_cfg.name, new_count)
    out = write_feed(feed_cfg, state, feed_dir, app.url_root, slug)
    log.info("[%s] wrote feed: %s", feed_cfg.name, out)


def run(app: AppConfig) -> None:
    app.output_dir.mkdir(parents=True, exist_ok=True)
    for feed_cfg in app.feeds:
        try:
            process_feed(app, feed_cfg)
        except Exception:
            log.exception("[%s] failed", feed_cfg.name)
