from __future__ import annotations

import logging

from .config import parse_args
from .pipeline import run


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = parse_args()
    run(app)


if __name__ == "__main__":
    main()
