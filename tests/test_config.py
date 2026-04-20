import textwrap

from rss2podcast.config import parse_args, slugify


def test_slugify():
    assert slugify("Ars Technica!") == "ars-technica"
    assert slugify("a/b c") == "a-b-c"


def test_cli_single_feed(tmp_path):
    cfg = parse_args([
        "--feed-url", "https://x.example/rss",
        "--feed-name", "X",
        "--output-dir", str(tmp_path),
        "--url-root", "https://pod.example/",
        "--voice", "en_US-amy-medium",
    ])
    assert len(cfg.feeds) == 1
    assert cfg.feeds[0].voice == "en_US-amy-medium"
    assert cfg.url_root == "https://pod.example"
    assert cfg.save_text is False


def test_save_text_flag(tmp_path):
    cfg = parse_args([
        "--feed-url", "https://x.example/rss",
        "--feed-name", "X",
        "--output-dir", str(tmp_path),
        "--url-root", "https://pod.example",
        "--save-text",
    ])
    assert cfg.save_text is True


def test_yaml_config(tmp_path):
    yml = tmp_path / "c.yaml"
    yml.write_text(textwrap.dedent("""
        output_dir: /tmp/out
        url_root: https://p.example
        tts_endpoint: http://tts:8080
        feeds:
          - name: A
            url: https://a.example/rss
            voice: v1
          - name: B
            url: https://b.example/rss
    """))
    cfg = parse_args(["--config", str(yml)])
    assert len(cfg.feeds) == 2
    assert cfg.feeds[0].voice == "v1"
    assert cfg.feeds[1].voice == "en_US-amy-medium"
