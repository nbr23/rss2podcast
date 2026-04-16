from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class FeedConfig:
    name: str
    url: str
    voice: str = "en_US-amy-low"
    description: str | None = None
    author: str | None = None
    image_url: str | None = None
    favor_recall: bool = True
    favor_precision: bool = False
    include_comments: bool = False
    include_tables: bool = False
    deduplicate: bool = False
    fast_extraction: bool = False
    prune_xpath: list[str] | None = None
    limit: int | None = None


@dataclass
class AppConfig:
    output_dir: Path
    url_root: str
    tts_endpoint: str
    feeds: list[FeedConfig] = field(default_factory=list)
    limit: int | None = None
    save_text: bool = False
    no_fetch: bool = False


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    return _SLUG_RE.sub("-", name.lower()).strip("-")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rss2podcast", description="RSS to TTS podcast generator")
    p.add_argument("--config", type=Path, help="YAML config file (multi-feed mode)")
    p.add_argument("--feed-url")
    p.add_argument("--feed-name")
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--url-root", help="Public base URL where output_dir is served")
    p.add_argument("--tts-endpoint", default="http://localhost:8080")
    p.add_argument("--voice", default="en_US-amy-low")
    p.add_argument("--description")
    p.add_argument("--author")
    p.add_argument("--image-url")
    p.add_argument("--limit", type=int, default=None, help="Process only the N newest articles per feed")
    p.add_argument(
        "--save-text",
        action="store_true",
        help="Persist the raw extracted body and the cleaned text sent to TTS in state.json",
    )
    p.add_argument(
        "--no-fetch",
        action="store_true",
        help="Disable trafilatura external crawling; use only RSS description/content",
    )

    ext = p.add_argument_group("extraction tuning")
    ext.add_argument(
        "--no-favor-recall",
        dest="favor_recall",
        action="store_false",
        default=True,
        help="Disable recall-biased extraction (trafilatura default is precision-biased)",
    )
    ext.add_argument(
        "--favor-precision",
        action="store_true",
        help="Bias trafilatura toward fewer, higher-confidence blocks (mutually exclusive with --favor-recall)",
    )
    ext.add_argument(
        "--include-comments",
        action="store_true",
        help="Include comment sections in extracted text",
    )
    ext.add_argument(
        "--include-tables",
        action="store_true",
        help="Include table content in extracted text",
    )
    ext.add_argument(
        "--deduplicate",
        action="store_true",
        help="Remove duplicate text blocks during extraction",
    )
    ext.add_argument(
        "--fast-extraction",
        action="store_true",
        help="Skip trafilatura fallback extractors (faster, may miss content)",
    )
    ext.add_argument(
        "--prune-xpath",
        action="append",
        metavar="XPATH",
        dest="prune_xpath",
        help="XPath expression to prune before extraction (repeatable); e.g. '//div[@class=\"author-bio\"]'",
    )
    return p


def parse_args(argv: list[str] | None = None) -> AppConfig:
    args = _build_parser().parse_args(argv)
    if args.config:
        app = _from_yaml(args.config)
        if args.limit is not None:
            app.limit = args.limit
        return app
    missing = [n for n in ("feed_url", "feed_name", "output_dir", "url_root") if not getattr(args, n)]
    if missing:
        raise SystemExit(f"missing required args: {', '.join('--' + m.replace('_', '-') for m in missing)}")
    feed = FeedConfig(
        name=args.feed_name,
        url=args.feed_url,
        voice=args.voice,
        description=args.description,
        author=args.author,
        image_url=args.image_url,
        favor_recall=args.favor_recall,
        favor_precision=args.favor_precision,
        include_comments=args.include_comments,
        include_tables=args.include_tables,
        deduplicate=args.deduplicate,
        fast_extraction=args.fast_extraction,
        prune_xpath=args.prune_xpath,
    )
    return AppConfig(
        output_dir=args.output_dir,
        url_root=args.url_root.rstrip("/"),
        tts_endpoint=args.tts_endpoint.rstrip("/"),
        feeds=[feed],
        limit=args.limit,
        save_text=args.save_text,
        no_fetch=args.no_fetch,
    )


def _from_yaml(path: Path) -> AppConfig:
    data = yaml.safe_load(path.read_text())
    feeds = [
        FeedConfig(
            name=f["name"],
            url=f["url"],
            voice=f.get("voice", "en_US-amy-low"),
            description=f.get("description"),
            author=f.get("author"),
            image_url=f.get("image_url"),
            favor_recall=f.get("favor_recall", True),
            favor_precision=f.get("favor_precision", False),
            include_comments=f.get("include_comments", False),
            include_tables=f.get("include_tables", False),
            deduplicate=f.get("deduplicate", False),
            fast_extraction=f.get("fast_extraction", False),
            prune_xpath=f.get("prune_xpath"),
            limit=f.get("limit"),
        )
        for f in data.get("feeds", [])
    ]
    return AppConfig(
        output_dir=Path(data["output_dir"]),
        url_root=data["url_root"].rstrip("/"),
        tts_endpoint=data.get("tts_endpoint", "http://localhost:8080").rstrip("/"),
        feeds=feeds,
        limit=data.get("limit"),
        save_text=data.get("save_text", False),
        no_fetch=data.get("no_fetch", False),
    )
