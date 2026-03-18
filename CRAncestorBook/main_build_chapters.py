# main_build_chapters.py

from pathlib import Path
from typing import Any
import tomllib
import requests
import logging

from CRAncestorBook.paths import prepare_chapter_env
from CRAncestorBook.core import configure_logging, load_book_context, prompt_toml_path
from CRAncestorBook.ai import load_prompt_library
from CRAncestorBook.chapter_pipeline_runtime.pipeline_registry import DEFAULT_PIPELINE_REGISTRY

from WrapEmit import emitter, status, progress, error, info, complete, configure_cli

logger = logging.getLogger(__name__)

def load_book_toml(path: Path) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid TOML: expected top-level table")
    return data


def parse_chapter_spec(spec: str, *, lower: int, upper: int) -> list[int]:
    raw = (spec or "").strip().lower()
    if raw == "all":
        return list(range(lower, upper + 1))

    chapters: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            raise ValueError("Empty chapter selection component")

        if "-" in token:
            a, b = token.split("-", 1)
            if not a.isdigit() or not b.isdigit():
                raise ValueError(f"Invalid range: {token!r}")
            start, end = int(a), int(b)
            if start < lower or end > upper or start > end:
                raise ValueError(f"Range out of bounds/invalid: {token!r}")
            chapters.update(range(start, end + 1))
        else:
            if not token.isdigit():
                raise ValueError(f"Invalid chapter: {token!r}")
            n = int(token)
            if not (lower <= n <= upper):
                raise ValueError(f"Invalid chapter: {n}. Must be {lower}-{upper}.")
            chapters.add(n)

    out = sorted(chapters)
    if not out:
        raise ValueError("No chapters selected")
    return out

def parse_steps_spec(spec: str, *, allowed: set[int]) -> list[int]:
    """
    Steps: "2", "3", "2-3", "2,3"
    Supported steps are controlled by caller-provided 'allowed'.
    """
    raw = (spec or "").strip().lower()
    if not raw:
        return [3]  # default keeps existing behavior

    # allowed = ALLOWED_STEPS
    steps: set[int] = set()

    for part in raw.split(","):
        token = part.strip()
        if not token:
            raise ValueError("Empty step selection component")

        if "-" in token:
            a, b = token.split("-", 1)
            if not a.isdigit() or not b.isdigit():
                raise ValueError(f"Invalid step range: {token!r}")
            start, end = int(a), int(b)
            if start > end:
                raise ValueError(f"Invalid step range: {token!r}")
            for s in range(start, end + 1):
                if s not in allowed:
                    raise ValueError(f"Unsupported step: {s}. Allowed: {sorted(allowed)}")
                steps.add(s)
        else:
            if not token.isdigit():
                raise ValueError(f"Invalid step: {token!r}")
            s = int(token)
            if s not in allowed:
                raise ValueError(f"Unsupported step: {s}. Allowed: {sorted(allowed)}")
            steps.add(s)

    out = sorted(steps)
    if not out:
        raise ValueError("No steps selected")
    return out


def main() -> None:
    configure_logging()
    configure_cli()

    try:
        book_toml_path = prompt_toml_path()
        if not book_toml_path.exists():
            error(f"Missing book TOML: {book_toml_path}")
            return

        # book_toml_path should now be the WORKSPACE TOML
        book_cfg = load_book_toml(book_toml_path)

        ctx = load_book_context(book_cfg)
        prompt_lib = load_prompt_library()

        run = book_cfg.get("run") or {}
        if not isinstance(run, dict) or run.get("chapters") is None:
            error('Missing [run].chapters in book.toml (e.g. "all" or "3" or "1-4")')
            return

        lower = min(ctx.chapters)
        upper = max(ctx.chapters)
        chapters = parse_chapter_spec(str(run["chapters"]), lower=lower, upper=upper)

        workspace_root = book_toml_path.parent.parent
        if ctx.root != workspace_root:
            info(f"ctx.root = {ctx.root}")
            info(f"workspace_root = {workspace_root}")
            error("Update book.toml so [paths].work_dir matches the current workspace.")
            return

        prepare_chapter_env(workspace_root, chapter_nums=sorted(ctx.chapters.keys()))

        steps = parse_steps_spec(
            str(run.get("steps") or ""),
            allowed=DEFAULT_PIPELINE_REGISTRY.allowed_steps(),
        )

        for step_n in steps:
            phase = DEFAULT_PIPELINE_REGISTRY.phase_for_step(step_n)
            info(f"Running Step {step_n}: {phase.label}")
            phase.run(ctx, chapters=chapters, prompt_lib=prompt_lib)

        info("\nDone.")

    except requests.exceptions.HTTPError as e:
        error(str(e))
        return


if __name__ == "__main__":
    main()
