# main_build_environment.py

# main_build_environment.py

from pathlib import Path
import logging

from CRAncestorBook.core import configure_logging, prompt_toml_path
from CRAncestorBook.paths import prepare_workspace_env, sync_workspace_from_toml

from WrapEmit import error, info, complete

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    toml_path = prompt_toml_path()
    if not toml_path.exists():
        error(f"Missing book TOML: {toml_path}")
        return

    try:
        workspace_root = sync_workspace_from_toml(toml_path)
        prepare_workspace_env(workspace_root)

        info(f"Workspace root: {workspace_root}")
        info(f"Workspace TOML: {workspace_root / 'book' / 'book.toml'}")
        complete("Environment build complete.")

    except Exception as e:
        logger.exception("Environment build failed")
        error(str(e))


if __name__ == "__main__":
    main()
