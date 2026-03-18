# main_build_toc.py

from pathlib import Path
import argparse
import logging

from WrapEmit import configure_cli

from CRAncestorBook.ai import load_prompt_library
from CRAncestorBook.toc_build import (
    build_toc_context,
    ensure_toc_env,
    verify_toc_prereqs,
)
from CRAncestorBook.toc_phases import run_phase_toc
from CRAncestorBook.core import configure_logging, load_book_context, prompt_toml_path

logger = logging.getLogger(__name__)

DEV_AUTO_APPROVE = True

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build biography chapter TOC artifacts from source materials."
    )

    parser.add_argument(
        "book_toml",
        nargs="?",
        type=Path,
        help="Path to book/book.toml",
    )

    parser.add_argument(
        "--prompt-json",
        type=Path,
        default=None,
        help="Optional prompt library JSON path. Defaults to configured prompt JSON.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run TOC steps even if their outputs already exist.",
    )

    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve draft chapters during development.",
    )

    parser.add_argument(
        "--start",
        dest="start_code",
        default=None,
        help="Start at this TOC step code (e.g. detect_breakpoints, generate_chapters).",
    )

    parser.add_argument(
        "--stop",
        dest="stop_code",
        default=None,
        help="Stop after this TOC step code.",
    )

    return parser


def main() -> None:
    configure_logging()
    configure_cli()

    parser = build_parser()
    args = parser.parse_args()

    if args.book_toml:
        book_toml_path = args.book_toml.expanduser().resolve()
    else:
        book_toml_path = prompt_toml_path()

    prompt_json_path = (
        args.prompt_json.expanduser().resolve() if args.prompt_json else None
    )

    logger.info("Starting TOC build for: %s", book_toml_path)

    ctx = build_toc_context(book_toml_path)
    ensure_toc_env(ctx)

    ok, msg = verify_toc_prereqs(ctx)
    if not ok:
        logger.error(msg)
        raise SystemExit(1)

    # Optional early validation that the prompt library is loadable.
    # run_phase_toc will load it again for actual use.
    load_prompt_library(prompt_json_path)

    run_phase_toc(
        ctx,
        force=args.force,
        start_code=args.start_code,
        stop_code=args.stop_code,
        prompt_library_path=prompt_json_path,
        # auto_approve=args.auto_approve,
        auto_approve=DEV_AUTO_APPROVE,
    )

    logger.info("Planning directory: %s", ctx.planning_dir)
    logger.info("Draft chapters: %s", ctx.draft_chapters_path)
    logger.info("Approved chapters: %s", ctx.approved_chapters_path)
    if ctx.generated_toml_exists:
        logger.info("Generated TOML: %s", ctx.generated_toml_path)
    else:
        logger.info("TOML not generated yet.")


if __name__ == "__main__":
    main()
