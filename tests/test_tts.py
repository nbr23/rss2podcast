import pytest
from pytest_httpserver import HTTPServer

from rss2podcast.tts import TTSClient


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("127.0.0.1", 0)


def test_synthesize_writes_mp3(tmp_path, httpserver: HTTPServer):
    fake_mp3 = b"ID3\x03" + b"\x00" * 1024
    httpserver.expect_request("/api/tts", method="POST").respond_with_data(
        fake_mp3, content_type="audio/mpeg"
    )
    client = TTSClient(httpserver.url_for("").rstrip("/"), voice="en_US-amy-medium")
    dest = tmp_path / "out.mp3"
    client.synthesize_to_file("hello world", dest)
    assert dest.read_bytes() == fake_mp3


def test_synthesize_cleans_tmp_on_failure(tmp_path, httpserver: HTTPServer):
    httpserver.expect_request("/api/tts", method="POST").respond_with_data(
        "boom", status=500
    )
    client = TTSClient(httpserver.url_for("").rstrip("/"), voice="en_US-amy-medium")
    dest = tmp_path / "out.mp3"
    with pytest.raises(Exception):
        client.synthesize_to_file("hello", dest)
    assert not dest.exists()
    assert list(tmp_path.glob(".tts-*.tmp")) == []
