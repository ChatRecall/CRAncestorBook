# toc_build/toc_builder.py

from pathlib import Path
import logging

from .toc_context import TOCContext

logger = logging.getLogger(__name__)


def build_toc_context(book_toml_path: str | Path) -> TOCContext:
    ctx = TOCContext.from_book_toml(book_toml_path)
    logger.info("Built TOCContext for project root: %s", ctx.project_root)
    return ctx


def verify_toc_prereqs(ctx: TOCContext) -> tuple[bool, str]:
    if not ctx.book_toml_path.exists():
        return False, f"Missing book TOML: {ctx.book_toml_path}"

    if not ctx.book_dir.exists():
        return False, f"Missing book directory: {ctx.book_dir}"

    if not ctx.sources_dir.exists():
        return False, f"Missing Sources directory: {ctx.sources_dir}"

    if not ctx.primary_sources_dir or not ctx.primary_sources_dir.exists():
        return False, (
            f"Missing required primary sources directory: {ctx.primary_sources_dir}\n"
            "Expected layout: Sources/primary"
        )

    if not ctx.has_any_sources:
        return False, "No source directories found for TOC planning."

    return True, ""


def ensure_toc_env(ctx: TOCContext) -> None:
    ctx.ensure_planning_dirs()
    logger.info("Ensured TOC planning directories under: %s", ctx.planning_dir)