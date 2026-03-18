# phases/enrichment/enrichment_decompose.py

import re
from typing import Any
import json
import logging

from CRAncestorBook.core import (
    BookContext,
    CODE_EPISODE_DECOMPOSE,
)
from CRAncestorBook.paths import chapter_path
from .enrichment_paths import _episode_index_path, _episode_eligibility_path

logger = logging.getLogger(__name__)

_EPISODE_SPLIT_RE = re.compile(r"(?m)^---EPISODE---\s*$")

def _parse_episode_decompose_output(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if not text:
        raise ValueError("episode_decompose output is empty")

    parts = _EPISODE_SPLIT_RE.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        raise ValueError("No episode blocks found in episode_decompose output")

    episodes: list[dict[str, Any]] = []
    allowed_categories = {"EVENT", "ROUTINE", "TRANSITION", "CONTEXT"}

    for i, block in enumerate(parts, start=1):
        lines = [line.rstrip() for line in block.splitlines()]

        if not lines:
            raise ValueError(f"Episode block {i} is empty")

        if not lines[0].startswith("CATEGORY:"):
            raise ValueError(f"Episode block {i} missing CATEGORY line")

        category = lines[0].replace("CATEGORY:", "", 1).strip()
        if category not in allowed_categories:
            raise ValueError(f"Episode block {i} has invalid category: {category}")

        if len(lines) < 2 or lines[1].strip() != "TEXT:":
            raise ValueError(f"Episode block {i} missing TEXT line")

        episode_text = "\n".join(lines[2:]).strip()
        if not episode_text:
            raise ValueError(f"Episode block {i} has empty TEXT")

        episodes.append({
            "episode_index": i,
            "category": category,
            "text": episode_text,
        })

    return episodes

def _parse_and_write_episode_index(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    decompose_path = chapter_path(ctx.root, chapter_n, CODE_EPISODE_DECOMPOSE)
    out_path = _episode_index_path(ctx, chapter_n)

    raw_text = decompose_path.read_text(encoding="utf-8")
    episodes = _parse_episode_decompose_output(raw_text)
    _validate_episode_count(chapter_n, episodes)

    out_path.write_text(
        json.dumps(episodes, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("Wrote parsed episode index: %s", out_path)
    logger.info("Parsed %d episodes for Chapter %d", len(episodes), chapter_n)
    return episodes

def _validate_episode_count(chapter_n: int, episodes: list[dict[str, Any]]) -> None:
    if len(episodes) < 3:
        raise ValueError(
            f"Chapter {chapter_n} episode count looks too low: {len(episodes)}"
        )

def _write_episode_eligibility(
    ctx: BookContext,
    chapter_n: int,
    episodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out_path = _episode_eligibility_path(ctx, chapter_n)

    rows: list[dict[str, Any]] = []
    for ep in episodes:
        category = ep["category"]
        eligible = category == "EVENT"

        rows.append({
            "episode_index": ep["episode_index"],
            "category": category,
            "eligible": eligible,
            "reason": "EVENT eligible in v1" if eligible else f"{category} not eligible in v1",
        })

    out_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("Wrote episode eligibility: %s", out_path)
    logger.info(
        "Eligible episodes for Chapter %d: %d/%d",
        chapter_n,
        sum(1 for r in rows if r["eligible"]),
        len(rows),
    )
    return rows

def _load_episode_index(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    path = _episode_index_path(ctx, chapter_n)
    return json.loads(path.read_text(encoding="utf-8"))

def _load_episode_eligibility(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    path = _episode_eligibility_path(ctx, chapter_n)
    return json.loads(path.read_text(encoding="utf-8"))

