from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from time import struct_time, mktime

import feedparser


@dataclass
class FeedEntry:
    guid: str
    title: str
    link: str
    pub_date: datetime
    summary_html: str | None
    content_html: str | None
    image_url: str | None = None


def _to_datetime(t: struct_time | None) -> datetime:
    if t is None:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(mktime(t), tz=timezone.utc)


def _guid_for(entry: dict) -> str:
    raw = entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title", "")
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _content_html(entry: dict) -> str | None:
    contents = entry.get("content")
    if contents:
        return contents[0].get("value")
    return None


def _entry_image_url(entry: dict) -> str | None:
    for m in entry.get("media_thumbnail", []):
        if url := m.get("url"):
            return url
    for m in entry.get("media_content", []):
        if m.get("type", "").startswith("image/") or m.get("medium") == "image":
            if url := m.get("url"):
                return url
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            if url := enc.get("href") or enc.get("url"):
                return url
    return None


def _feed_image_url(feed: dict) -> str | None:
    img = feed.get("image")
    if img:
        return img.get("href") or None
    return None


def fetch(url: str) -> tuple[list[FeedEntry], str | None]:
    parsed = feedparser.parse(url)
    out: list[FeedEntry] = []
    for e in parsed.entries:
        out.append(
            FeedEntry(
                guid=_guid_for(e),
                title=e.get("title", "(untitled)"),
                link=e.get("link", ""),
                pub_date=_to_datetime(e.get("published_parsed") or e.get("updated_parsed")),
                summary_html=e.get("summary"),
                content_html=_content_html(e),
                image_url=_entry_image_url(e),
            )
        )
    return out, _feed_image_url(parsed.feed)
