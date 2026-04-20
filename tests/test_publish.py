from datetime import datetime, timezone

from rss2podcast.config import FeedConfig
from rss2podcast.publish import write_feed
from rss2podcast.state import State


def test_writes_valid_rss(tmp_path):
    feed_dir = tmp_path / "myfeed"
    feed_dir.mkdir()
    state = State(feed_url="https://src.example/rss", path=feed_dir / "state.json")
    state.entries["guid-1"] = {
        "title": "Episode One",
        "link": "https://src.example/articles/1",
        "pub_date": datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc).isoformat(),
        "description": "Summary text",
        "mp3_filename": "2026-01-01-abc.mp3",
        "filesize": 12345,
        "duration_seconds": 125,
    }

    cfg = FeedConfig(name="MyFeed", url="https://src.example/rss", description="Test", author="Tester")
    out = write_feed(cfg, state, feed_dir, "https://podcasts.example.com", "myfeed")
    assert out == tmp_path / "myfeed.xml"
    xml = out.read_text()
    assert "<title>MyFeed</title>" in xml
    assert "Episode One" in xml
    assert "https://podcasts.example.com/myfeed/2026-01-01-abc.mp3" in xml
    assert 'length="12345"' in xml
    assert "audio/mpeg" in xml
    assert "0:02:05" in xml
    assert "https://src.example/articles/1" in xml
