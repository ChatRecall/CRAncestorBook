# helpers.py
from pathlib import Path

from .constants import DEFAULT_BOOK_TOML

import logging

def configure_logging(default_level: int = logging.DEBUG) -> None:
    """
    Configure logging for CLI runs, but don't stomp on a parent app's logging config.
    Safe if this module is imported by a higher-level main.
    """
    root = logging.getLogger()
    if root.handlers:
        # Someone else already configured logging (likely a parent app)
        return

    logging.basicConfig(
        level=default_level,
        format="%(name)s - %(levelname)s - %(message)s (line: %(lineno)d)",
        handlers=[logging.StreamHandler()],
    )

    # Quiet noisy libs (only applies if we're the one configuring)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("WrapAI").setLevel(logging.INFO)


def prompt_toml_path() -> Path:
    raw = input(f"book.toml path [{DEFAULT_BOOK_TOML}]: ").strip()
    return Path(raw).expanduser() if raw else DEFAULT_BOOK_TOML

