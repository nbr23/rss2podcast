from __future__ import annotations

import logging
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .config import parse_args
from .pipeline import run


def _version() -> str:
    try:
        return version("rss2podcast")
    except PackageNotFoundError:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger(__name__).info("rss2podcast %s", _version())
    app = parse_args()
    run(app)


if __name__ == "__main__":
    main()
