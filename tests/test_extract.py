from rss2podcast.extract import html_to_text


def test_strips_script_and_style():
    html = "<p>Hello</p><script>alert(1)</script><style>.x{}</style>"
    assert "alert" not in html_to_text(html)
    assert "Hello" in html_to_text(html)


def test_drops_code_blocks():
    html = "<p>Intro</p><pre><code>x = 1</code></pre><p>Outro</p>"
    out = html_to_text(html)
    assert "x = 1" not in out
    assert "Intro" in out
    assert "Outro" in out


def test_collapses_whitespace():
    html = "<p>a   b\t\tc</p>"
    out = html_to_text(html)
    assert "a b c" in out
