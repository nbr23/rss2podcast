from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from feedgen.feed import FeedGenerator

from .config import FeedConfig
from .state import State


def _format_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


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

    channel_link = f"{url_root}/{quote(feed_slug)}/feed.xml"
    fg.id(channel_link)
    fg.title(feed_cfg.name)
    fg.link(href=channel_link, rel="self")
    if feed_cfg.url:
        fg.link(href=feed_cfg.url, rel="alternate")
    fg.description(feed_cfg.description or f"TTS podcast generated from {feed_cfg.url}")
    lang = feed_cfg.voice.split("_")[0] if "_" in feed_cfg.voice else "en"
    fg.language(lang)
    if feed_cfg.author:
        fg.author({"name": feed_cfg.author})
        fg.podcast.itunes_author(feed_cfg.author)
    if feed_cfg.image_url:
        fg.image(feed_cfg.image_url)
        fg.podcast.itunes_image(feed_cfg.image_url)
    fg.podcast.itunes_category("Technology")
    fg.podcast.itunes_explicit("no")

    items = sorted(
        state.entries.items(),
        key=lambda kv: kv[1].get("pub_date", ""),
        reverse=True,
    )

    for guid, rec in items:
        fe = fg.add_entry()
        fe.id(guid)
        fe.title(rec.get("title", "(untitled)"))
        if rec.get("link"):
            fe.link(href=rec["link"])
        if rec.get("description"):
            fe.description(rec["description"])
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

    out = feed_dir / "feed.xml"
    xml_bytes = fg.rss_str(pretty=True)
    if style:
        pi = b'<?xml-stylesheet type="text/xsl" href="../style.xsl"?>\n'
        nl = xml_bytes.index(b'\n')
        xml_bytes = xml_bytes[:nl + 1] + pi + xml_bytes[nl + 1:]
    out.write_bytes(xml_bytes)
    return out
