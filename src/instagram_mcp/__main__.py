from __future__ import annotations

import logging
import sys

from .server import mcp


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    mcp.run()


if __name__ == "__main__":
    main()
