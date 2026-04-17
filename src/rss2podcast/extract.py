from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import trafilatura
from bs4 import BeautifulSoup
from lxml import etree, html as lxml_html

from .feed import FeedEntry

log = logging.getLogger(__name__)

_WS_RE = re.compile(r"[ \t]+")
_NEWLINES_RE = re.compile(r"\n{3,}")
_MIN_EXTRACTED_CHARS = 200


@dataclass
class ExtractedBody:
    raw: str
    clean: str
    source: str


_INLINE_TAGS = ["b", "strong", "i", "em", "u", "s", "span", "a", "small", "mark", "sub", "sup"]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "pre", "code", "figure", "img", "iframe", "noscript"]):
        tag.decompose()
    for tag in soup(_INLINE_TAGS):
        tag.unwrap()
    soup.smooth()
    text = soup.get_text(separator="\n")
    text = _WS_RE.sub(" ", text)
    text = _NEWLINES_RE.sub("\n\n", text)
    return text.strip()


def _merge_split_containers(html_text: str, xpaths: list[str]) -> str:
    try:
        root = lxml_html.fromstring(html_text)
    except (etree.ParserError, ValueError) as e:
        log.warning("merge_xpath: could not parse HTML (%s), skipping merge", e)
        return html_text
    merged_any = False
    for xp in xpaths:
        try:
            matches = root.xpath(xp)
        except etree.XPathEvalError as e:
            log.warning("merge_xpath: invalid xpath %r (%s), skipping", xp, e)
            continue
        matches = [m for m in matches if isinstance(m, etree._Element)]
        if len(matches) < 2:
            continue
        target = matches[0]
        for extra in matches[1:]:
            if extra.text:
                if len(target) > 0:
                    tail = target[-1]
                    tail.tail = (tail.tail or "") + extra.text
                else:
                    target.text = (target.text or "") + extra.text
            for child in list(extra):
                target.append(child)
            parent = extra.getparent()
            if parent is not None:
                parent.remove(extra)
        log.info("merge_xpath: merged %d containers for %r", len(matches), xp)
        merged_any = True
    if not merged_any:
        return html_text
    return lxml_html.tostring(root, encoding="unicode")


def extract_body(
    entry: FeedEntry,
    fetch_full: bool = True,
    favor_recall: bool = True,
    favor_precision: bool = False,
    include_comments: bool = False,
    include_tables: bool = False,
    deduplicate: bool = False,
    fast_extraction: bool = False,
    prune_xpath: list[str] | None = None,
    merge_xpath: list[str] | None = None,
) -> ExtractedBody:
    if fetch_full and entry.link:
        log.info("trafilatura: fetching %s", entry.link)
        try:
            downloaded = trafilatura.fetch_url(entry.link)
            if not downloaded:
                log.warning("trafilatura: empty download for %s, falling back to RSS content", entry.link)
            else:
                extract_input = _merge_split_containers(downloaded, merge_xpath) if merge_xpath else downloaded
                extracted = trafilatura.extract(
                    extract_input,
                    favor_recall=favor_recall,
                    favor_precision=favor_precision,
                    include_comments=include_comments,
                    include_tables=include_tables,
                    deduplicate=deduplicate,
                    fast=fast_extraction,
                    prune_xpath=prune_xpath,
                )
                if not extracted:
                    log.warning("trafilatura: extraction returned nothing for %s, falling back to RSS content", entry.link)
                else:
                    extracted_clean = extracted.strip()
                    if len(extracted_clean) < _MIN_EXTRACTED_CHARS:
                        log.warning(
                            "trafilatura: extracted only %d chars from %s (below %d threshold), falling back to RSS content",
                            len(extracted_clean), entry.link, _MIN_EXTRACTED_CHARS,
                        )
                    else:
                        log.info("trafilatura: extracted %d chars from %s", len(extracted_clean), entry.link)
                        return ExtractedBody(raw=downloaded, clean=extracted_clean, source="trafilatura")
        except Exception as e:
            log.warning("trafilatura: failed for %s: %s — falling back to RSS content", entry.link, e)
    elif not fetch_full:
        log.info("external fetch disabled, using RSS content directly")
    else:
        log.info("entry has no link, using RSS content directly")

    html = entry.content_html or entry.summary_html or ""
    if not html:
        log.warning("no content available for entry %s (no link, no RSS content/summary)", entry.guid)
        return ExtractedBody(raw="", clean="", source="none")
    source = "rss-content" if entry.content_html else "rss-summary"
    text = html_to_text(html)
    log.info("RSS fallback: using %s field, %d chars after cleanup", source, len(text))
    return ExtractedBody(raw=html, clean=text, source=source)


def compose_speech(
    entry: FeedEntry,
    fetch_full: bool = True,
    favor_recall: bool = True,
    favor_precision: bool = False,
    include_comments: bool = False,
    include_tables: bool = False,
    deduplicate: bool = False,
    fast_extraction: bool = False,
    prune_xpath: list[str] | None = None,
    merge_xpath: list[str] | None = None,
) -> tuple[str, ExtractedBody]:
    body = extract_body(
        entry,
        fetch_full=fetch_full,
        favor_recall=favor_recall,
        favor_precision=favor_precision,
        include_comments=include_comments,
        include_tables=include_tables,
        deduplicate=deduplicate,
        fast_extraction=fast_extraction,
        prune_xpath=prune_xpath,
        merge_xpath=merge_xpath,
    )
    if body.clean:
        return f"{entry.title}.\n\n{body.clean}", body
    return entry.title, body
