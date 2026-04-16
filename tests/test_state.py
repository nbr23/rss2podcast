from rss2podcast.state import State


def test_load_missing_file_returns_empty(tmp_path):
    s = State.load(tmp_path / "state.json", "https://example.com/rss")
    assert s.entries == {}
    assert s.feed_url == "https://example.com/rss"


def test_add_persists_and_dedups(tmp_path):
    p = tmp_path / "state.json"
    s = State.load(p, "https://example.com/rss")
    s.add("guid-1", {"title": "Hello"})
    assert s.has("guid-1")

    s2 = State.load(p, "https://example.com/rss")
    assert s2.has("guid-1")
    assert s2.entries["guid-1"]["title"] == "Hello"


def test_save_is_atomic(tmp_path):
    p = tmp_path / "state.json"
    s = State.load(p, "url")
    s.add("g", {"x": 1})
    leftover = list(tmp_path.glob(".state-*.tmp"))
    assert leftover == []
