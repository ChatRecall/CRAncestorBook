# phases/enrichment/enrichment_review.py

import logging
from typing import Any
import json

from CRAncestorBook.core import BookContext
from .enrichment_paths import _episode_retrieval_review_path
from .enrichment_retrieval import _load_episode_retrieval

logger = logging.getLogger(__name__)

def _review_label_for_retrieval(row: dict[str, Any]) -> tuple[str, str]:
    if not row.get("eligible", False):
        return "skip", row.get("skip_reason", "Not eligible")

    filtered_hits = int(row.get("filtered_hits", 0) or 0)
    filtered_sources = int(row.get("filtered_sources", 0) or 0)
    best = row.get("best_overall", None)
    citations = row.get("citations", []) or []

    if filtered_hits <= 0:
        return "none", "No filtered retrieval hits"

    if best is None:
        return "weak", "Missing best_overall distance"

    try:
        best = float(best)
    except Exception:
        return "weak", "Invalid best_overall distance"

    unique_sources = {
        c.get("source_id")
        for c in citations
        if isinstance(c, dict) and c.get("source_id")
    }
    source_count = len(unique_sources)

    # Strong: very good nearest match, even if only one source
    if best <= 0.32:
        if source_count >= 2 or filtered_sources >= 2:
            return "strong", "Strong distance with multi-source support"
        return "strong", "Strong distance with narrow support"

    # Mixed: good enough nearest match, even if only one source
    if best <= 0.45:
        if source_count >= 2 or filtered_sources >= 2:
            return "mixed", "Moderate distance with multi-source support"
        return "mixed", "Moderate distance with narrow support"

    # Borderline mixed: weaker best match, but more than one filtered hit
    if best <= 0.50 and filtered_hits >= 2:
        if source_count >= 2 or filtered_sources >= 2:
            return "mixed", "Borderline distance with repeated support"
        return "mixed", "Borderline distance with repeated hits"

    # Weak: weak best match and/or noisy support
    return "weak", "Weak or noisy retrieval"

def _run_episode_retrieval_review(
    ctx: BookContext,
    chapter_n: int,
) -> list[dict[str, Any]]:
    retrieval_rows = _load_episode_retrieval(ctx, chapter_n)
    out_rows: list[dict[str, Any]] = []

    for row in retrieval_rows:
        label, reason = _review_label_for_retrieval(row)

        out_rows.append({
            "episode_index": row.get("episode_index"),
            "category": row.get("category"),
            "eligible": row.get("eligible", False),
            "retrieval_ok": row.get("retrieval_ok", False),
            "review_label": label,
            "review_reason": reason,
            "raw_sources": row.get("raw_sources", 0),
            "raw_hits": row.get("raw_hits", 0),
            "filtered_sources": row.get("filtered_sources", 0),
            "filtered_hits": row.get("filtered_hits", 0),
            "best_overall": row.get("best_overall"),
            "citation_count": len(row.get("citations", []) or []),
        })

    out_path = _episode_retrieval_review_path(ctx, chapter_n)
    out_path.write_text(
        json.dumps(out_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts: dict[str, int] = {}
    for row in out_rows:
        label = row["review_label"]
        counts[label] = counts.get(label, 0) + 1

    logger.info("Wrote episode retrieval review: %s", out_path)
    logger.info(
        "Episode retrieval review counts for Chapter %d: %s",
        chapter_n,
        counts,
    )
    return out_rows

# episode retrieval review
def _load_episode_retrieval_review(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    path = _episode_retrieval_review_path(ctx, chapter_n)
    return json.loads(path.read_text(encoding="utf-8"))
