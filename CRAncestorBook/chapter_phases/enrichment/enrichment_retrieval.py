# phases/enrichment/enrichment_retrieval.py

import json
from typing import Any
import logging

from WrapEmbed import query_context
from WrapEmit import status

from CRAncestorBook.core import BookContext
from .enrichment_decompose import _load_episode_index, _load_episode_eligibility
from .enrichment_paths import _episode_retrieval_path

logger = logging.getLogger(__name__)

def _citation_to_dict(c: Any) -> dict[str, Any]:
    if isinstance(c, dict):
        return c

    out: dict[str, Any] = {}
    for name in (
        "source_id",
        "source_title",
        "source_type",
        "chunk_index",
        "chunk_id",
        "distance",
        "dist",
    ):
        if hasattr(c, name):
            out[name] = getattr(c, name)
    return out

def _best_overall_from_citations(citations: list[dict[str, Any]]) -> float | None:
    vals: list[float] = []

    for c in citations:
        if "distance" in c and isinstance(c["distance"], (int, float)):
            vals.append(float(c["distance"]))
        elif "dist" in c and isinstance(c["dist"], (int, float)):
            vals.append(float(c["dist"]))

    return min(vals) if vals else None

def _run_episode_retrieval(
    ctx: BookContext,
    chapter_n: int,
    *,
    embedder: Any,
) -> list[dict[str, Any]]:
    episodes = _load_episode_index(ctx, chapter_n)
    eligibility_rows = _load_episode_eligibility(ctx, chapter_n)
    eligibility_by_index = {
        row["episode_index"]: row
        for row in eligibility_rows
    }

    out_rows: list[dict[str, Any]] = []

    for ep in episodes:
        ep_index = ep["episode_index"]
        category = ep["category"]
        ep_text = ep["text"]

        elig = eligibility_by_index.get(ep_index)
        eligible = bool(elig and elig.get("eligible"))

        if not eligible:
            out_rows.append({
                "episode_index": ep_index,
                "category": category,
                "eligible": False,
                "retrieval_ok": False,
                "skip_reason": elig.get("reason") if elig else "No eligibility row found",
            })
            continue

        status(f"Chapter {chapter_n}: Episode Retrieval {ep_index}")

        result = query_context(
            embedder=embedder,
            query=ep_text,
            where=None,
            debug=False,
        )

        citations = [_citation_to_dict(c) for c in result.citations]

        row = {
            "episode_index": ep_index,
            "category": category,
            "eligible": True,
            "query_text": ep_text,
            "retrieval_ok": result.filtered_hits > 0,
            "raw_sources": result.raw_sources,
            "raw_hits": result.raw_hits,
            "filtered_sources": result.filtered_sources,
            "filtered_hits": result.filtered_hits,
            "best_overall": (
                result.best_overall
                if hasattr(result, "best_overall")
                else _best_overall_from_citations(citations)
            ),
            "context_text": result.context_text,
            "citations": citations,
        }
        out_rows.append(row)

    out_path = _episode_retrieval_path(ctx, chapter_n)
    out_path.write_text(
        json.dumps(out_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("Wrote episode retrieval: %s", out_path)
    logger.info(
        "Retrieved eligible episodes for Chapter %d: %d/%d",
        chapter_n,
        sum(1 for r in out_rows if r.get("eligible")),
        len(out_rows),
    )
    return out_rows

def _load_episode_retrieval(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    path = _episode_retrieval_path(ctx, chapter_n)
    return json.loads(path.read_text(encoding="utf-8"))

