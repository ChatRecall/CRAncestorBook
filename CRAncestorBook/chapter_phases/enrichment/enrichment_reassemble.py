# phases/enrichment/enrichment_reassemble.py

from pathlib import Path
from typing import Any
import json
import logging

from CRAncestorBook.core import BookContext
from .enrichment_paths import _episode_decisions_path, _episode_reassembled_path

logger = logging.getLogger(__name__)

def _load_decision_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError(f"Expected JSON list in {path}")
    return data

def _run_episode_reassembly(
    ctx: BookContext,
    chapter_n: int,
) -> Path:
    decision_rows = _load_decision_rows(_episode_decisions_path(ctx, chapter_n))

    parts: list[str] = []
    for row in decision_rows:
        text = (row.get("final_text") or "").strip()
        if text:
            parts.append(text)

    chapter_text = "\n\n".join(parts).strip() + "\n"

    out_path = _episode_reassembled_path(ctx, chapter_n)
    out_path.write_text(chapter_text, encoding="utf-8")

    logger.info("Wrote episode reassembled chapter: %s", out_path)
    logger.info(
        "Episode reassembly for Chapter %d: paragraphs=%d chars=%d",
        chapter_n,
        len(parts),
        len(chapter_text),
    )
    return out_path

