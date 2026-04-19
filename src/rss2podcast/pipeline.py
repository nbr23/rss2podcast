from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from mutagen.mp3 import MP3

from .config import AppConfig, FeedConfig, slugify
from .extract import compose_speech, html_to_text
from .feed import fetch
from .publish import write_feed
from .state import State
from .templates.style import render_feed_style
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
    entries, feed_image, channel_link = fetch(feed_cfg.url)
    dirty = False
    if feed_image and not state.feed_image_url:
        state.feed_image_url = feed_image
        dirty = True
    if channel_link and not state.feed_channel_link:
        state.feed_channel_link = channel_link
        dirty = True
    if dirty:
        state.save()
    limit = feed_cfg.limit if feed_cfg.limit is not None else app.limit
    if limit is not None:
        entries = entries[:limit]

    state_dirty = False
    for idx, entry in enumerate(entries):
        if entry.guid in state.entries and state.entries[entry.guid].get("feed_index") != idx:
            state.entries[entry.guid]["feed_index"] = idx
            state_dirty = True
    if state_dirty:
        state.save()
    log.info("[%s] %d entries in feed, %d already in state", feed_cfg.name, len(entries), len(state.entries))

    tts = TTSClient(app.tts_endpoint, feed_cfg.voice)

    new_count = 0
    for idx, entry in enumerate(entries):
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
            merge_xpath=feed_cfg.merge_xpath,
        )
        if not text.strip():
            log.warning("[%s] empty text for %s, skipping", feed_cfg.name, entry.guid)
            continue

        date_prefix = entry.pub_date.strftime("%Y-%m-%d")
        title_slug = slugify(entry.title)[:60].strip("-")
        guid_short = entry.guid[:8]
        mp3_filename = (
            f"{date_prefix}-{title_slug}-{guid_short}.mp3" if title_slug else f"{date_prefix}-{guid_short}.mp3"
        )
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
            "description": html_to_text(entry.summary_html) if entry.summary_html else "",
            "mp3_filename": mp3_filename,
            "filesize": mp3_path.stat().st_size,
            "duration_seconds": _mp3_duration(mp3_path),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "text_source": body.source,
            "feed_index": idx,
        }
        if entry.image_url:
            record["image_url"] = entry.image_url
        if app.save_text:
            record["raw_text"] = body.raw
            record["tts_text"] = text
        state.add(entry.guid, record)
        new_count += 1

    log.info("[%s] processed %d new entries", feed_cfg.name, new_count)

    if limit is not None:
        current_guids = {e.guid for e in entries}
        stale = [g for g in state.entries if g not in current_guids]
        if stale:
            for g in stale:
                del state.entries[g]
            state.save()

    out = write_feed(feed_cfg, state, feed_dir, app.url_root, slug, style=app.style_rss_feed)
    log.info("[%s] wrote feed: %s", feed_cfg.name, out)


def run(app: AppConfig) -> None:
    app.output_dir.mkdir(parents=True, exist_ok=True)
    if app.style_rss_feed:
        (app.output_dir / "style.xsl").write_text(render_feed_style(app.show_github_ribbon))
    for feed_cfg in app.feeds:
        try:
            process_feed(app, feed_cfg)
        except Exception:
            log.exception("[%s] failed", feed_cfg.name)
