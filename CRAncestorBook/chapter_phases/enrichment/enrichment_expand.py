# phases/enrichment/enrichment_expand.py

import logging
from typing import Any
import json

from WrapEmit import status

from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import get_model_substep
from CRAncestorBook.core import BookContext, CODE_EPISODE_EXPAND
from .enrichment_ai import _render_prompt_from_library, _call_runner_text
from .enrichment_paths import _episode_expansions_path
from .enrichment_retrieval import _load_episode_retrieval
from .enrichment_review import _load_episode_retrieval_review

logger = logging.getLogger(__name__)

def _run_episode_expansions(
    ctx: BookContext,
    chapter_n: int,
    *,
    prompt_lib: Any,
) -> list[dict[str, Any]]:
    retrieval_rows = _load_episode_retrieval(ctx, chapter_n)
    review_rows = _load_episode_retrieval_review(ctx, chapter_n)
    review_by_index = {
        row["episode_index"]: row
        for row in review_rows
    }

    chapter = ctx.chapter(chapter_n)
    chapter_examples = "\n".join(f"- {x}" for x in chapter.examples)

    out_rows: list[dict[str, Any]] = []

    ai_model = get_model_substep(CODE_EPISODE_EXPAND)
    prompt_name = "chapter_episode_expand_vector"

    logger.info("Episode expand AI Model: %s", ai_model)

    for row in retrieval_rows:
        ep_index = row.get("episode_index")
        category = row.get("category")
        ep_text = row.get("query_text", "")
        review = review_by_index.get(ep_index, {})

        review_label = review.get("review_label", "skip")
        review_reason = review.get("review_reason", "No retrieval review row found")

        if review_label not in {"strong", "mixed"}:
            out_rows.append({
                "episode_index": ep_index,
                "category": category,
                "eligible": row.get("eligible", False),
                "review_label": review_label,
                "review_reason": review_reason,
                "expand_ok": False,
                "skip_reason": f"review_label={review_label} not approved for expansion",
            })
            continue

        if not row.get("retrieval_ok", False):
            out_rows.append({
                "episode_index": ep_index,
                "category": category,
                "eligible": row.get("eligible", False),
                "review_label": review_label,
                "review_reason": review_reason,
                "expand_ok": False,
                "skip_reason": "retrieval_ok is false",
            })
            continue

        status(f"Chapter {chapter_n}: Episode Expand {ep_index}")

        values = {
            "episode_text": ep_text,
            "context_text": row.get("context_text", ""),
            "chapter_title": chapter.title,
            "chapter_time_range": chapter.time_range,
            "chapter_examples": chapter_examples,
        }

        user_prompt, system_prompt, attrs = _render_prompt_from_library(
            prompt_lib=prompt_lib,
            prompt_name=prompt_name,
            values=values,
        )

        runner = build_runner(ai_model=ai_model)
        runner.set_attributes(**attrs)

        candidate_text = _call_runner_text(
            runner=runner,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
        )

        out_rows.append({
            "episode_index": ep_index,
            "category": category,
            "eligible": row.get("eligible", False),
            "review_label": review_label,
            "review_reason": review_reason,
            "expand_ok": True,
            "episode_text": ep_text,
            "candidate_text": candidate_text,
            "retrieval_filtered_sources": row.get("filtered_sources", 0),
            "retrieval_filtered_hits": row.get("filtered_hits", 0),
            "retrieval_best_overall": row.get("best_overall"),
            "citation_count": len(row.get("citations", []) or []),
            "citations": row.get("citations", []),
        })

    out_path = _episode_expansions_path(ctx, chapter_n)
    out_path.write_text(
        json.dumps(out_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts: dict[str, int] = {"expanded": 0, "skipped": 0}
    for row in out_rows:
        if row.get("expand_ok"):
            counts["expanded"] += 1
        else:
            counts["skipped"] += 1

    logger.info("Wrote episode expansions: %s", out_path)
    logger.info(
        "Episode expansion counts for Chapter %d: %s",
        chapter_n,
        counts,
    )
    return out_rows

# Episode evaluation
def _load_episode_expansions(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    path = _episode_expansions_path(ctx, chapter_n)
    return json.loads(path.read_text(encoding="utf-8"))


