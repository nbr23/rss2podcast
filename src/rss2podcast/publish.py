from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from feedgen.feed import FeedGenerator

from .config import FeedConfig
from .state import State

log = logging.getLogger(__name__)


def _format_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def _set_itunes_image(podcast_ext, url: str, context: str) -> None:
    lower = url.split("?", 1)[0].lower()
    if lower.endswith((".jpg", ".png")):
        podcast_ext.itunes_image(url)
        return
    if lower.endswith(".jpeg"):
        mangled = f"_{type(podcast_ext).__name__}__itunes_image"
        setattr(podcast_ext, mangled, url)
        return
    log.warning("skipping itunes_image for %s: unsupported extension (url=%s)", context, url)


def write_feed(
    feed_cfg: FeedConfig,
    state: State,
    feed_dir: Path,
    url_root: str,
    feed_slug: str,
    style: bool = False,
) -> Path:
    fg = FeedGenerator()
    fg.load_extension("podcast")

    channel_link = f"{url_root}/{quote(feed_slug)}.xml"
    fg.id(channel_link)
    fg.title(feed_cfg.name)
    fg.link(href=channel_link, rel="self")
    alternate = state.feed_channel_link or feed_cfg.url
    if alternate:
        fg.link(href=alternate, rel="alternate")
    fg.description(feed_cfg.description or f"TTS podcast generated from {feed_cfg.url}")
    lang = feed_cfg.voice.split("_")[0] if "_" in feed_cfg.voice else "en"
    fg.language(lang)
    if feed_cfg.author:
        fg.author({"name": feed_cfg.author})
        fg.podcast.itunes_author(feed_cfg.author)
    channel_image = feed_cfg.image_url or state.feed_image_url
    if channel_image:
        fg.image(channel_image)
        _set_itunes_image(fg.podcast, channel_image, "channel")
    fg.podcast.itunes_category("Technology")
    fg.podcast.itunes_explicit("no")

    in_feed = [kv for kv in state.entries.items() if kv[1].get("feed_index") is not None]
    in_feed.sort(key=lambda kv: kv[1]["feed_index"])
    stale = [kv for kv in state.entries.items() if kv[1].get("feed_index") is None]
    stale.sort(key=lambda kv: kv[1].get("pub_date", ""), reverse=True)
    items = in_feed + stale

    for guid, rec in items:
        fe = fg.add_entry(order="append")
        fe.id(guid)
        fe.title(rec.get("title", "(untitled)"))
        if rec.get("link"):
            fe.link(href=rec["link"])
        desc = rec.get("description", "")
        link = rec.get("link")
        if link:
            anchor = f'<a href="{link}">{link}</a>'
            desc = f"{desc}<br/><br/>{anchor}" if desc else anchor
        if desc:
            fe.description(desc)
        pub = rec.get("pub_date")
        if pub:
            try:
                fe.pubDate(datetime.fromisoformat(pub))
            except ValueError:
                fe.pubDate(datetime.now(timezone.utc))
        mp3_url = f"{url_root}/{quote(feed_slug)}/{quote(rec['mp3_filename'])}"
        fe.enclosure(mp3_url, str(rec.get("filesize", 0)), "audio/mpeg")
        if rec.get("duration_seconds"):
            fe.podcast.itunes_duration(_format_duration(rec["duration_seconds"]))
        if rec.get("image_url"):
            _set_itunes_image(fe.podcast, rec["image_url"], guid)

    out = feed_dir.parent / f"{feed_dir.name}.xml"
    xml_bytes = fg.rss_str(pretty=True)
    if style:
        pi = b'<?xml-stylesheet type="text/xsl" href="style.xsl"?>\n'
        nl = xml_bytes.index(b'\n')
        xml_bytes = xml_bytes[:nl + 1] + pi + xml_bytes[nl + 1:]
    out.write_bytes(xml_bytes)
    return out
