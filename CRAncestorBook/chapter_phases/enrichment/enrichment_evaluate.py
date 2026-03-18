# phases/enrichment/enrichment_evaluate.py

import json
from typing import Any
import logging

from WrapEmit import status

from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import get_model_substep
from CRAncestorBook.core import BookContext, CODE_EPISODE_EVALUATE
from .enrichment_ai import _render_prompt_from_library, _call_runner_text
from .enrichment_expand import _load_episode_expansions
from .enrichment_paths import _episode_evaluations_path
from .enrichment_retrieval import _load_episode_retrieval
from .enrichment_review import _load_episode_retrieval_review

logger = logging.getLogger(__name__)

def _parse_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Evaluation model returned empty output.")

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Evaluation output is not valid JSON: {exc}") from exc

    if not isinstance(obj, dict):
        raise RuntimeError("Evaluation output must be a JSON object.")

    return obj

def _validate_episode_evaluation_obj(obj: dict[str, Any]) -> dict[str, Any]:
    required_bool_keys = [
        "grounded",
        "scope_creep",
        "merges_other_episodes",
        "meaning_changed",
        "adds_supported_detail",
        "candidate_is_materially_better",
        "recommend_accept",
    ]

    required_list_keys = [
        "reasons",
        "supported_details",
        "unsupported_or_risky_details",
    ]

    missing = [k for k in required_bool_keys + required_list_keys if k not in obj]
    if missing:
        raise RuntimeError(f"Evaluation JSON missing required keys: {missing}")

    for key in required_bool_keys:
        if not isinstance(obj[key], bool):
            raise RuntimeError(f"Evaluation key '{key}' must be boolean.")

    for key in required_list_keys:
        if not isinstance(obj[key], list):
            raise RuntimeError(f"Evaluation key '{key}' must be a list.")
        for i, item in enumerate(obj[key]):
            if not isinstance(item, str):
                raise RuntimeError(
                    f"Evaluation key '{key}' item {i} must be a string."
                )

    return obj

def _run_episode_evaluations(
    ctx: BookContext,
    chapter_n: int,
    *,
    prompt_lib: Any,
) -> list[dict[str, Any]]:
    expansion_rows = _load_episode_expansions(ctx, chapter_n)
    review_rows = _load_episode_retrieval_review(ctx, chapter_n)
    retrieval_rows = _load_episode_retrieval(ctx, chapter_n)

    review_by_index = {
        row["episode_index"]: row
        for row in review_rows
    }
    retrieval_by_index = {
        row["episode_index"]: row
        for row in retrieval_rows
    }

    chapter = ctx.chapter(chapter_n)
    chapter_examples = "\n".join(f"- {x}" for x in chapter.examples)

    out_rows: list[dict[str, Any]] = []

    ai_model = get_model_substep(CODE_EPISODE_EVALUATE)
    prompt_name = "chapter_episode_evaluate"

    logger.info("Episode evaluate AI Model: %s", ai_model)

    for row in expansion_rows:
        ep_index = row.get("episode_index")
        category = row.get("category")
        expand_ok = bool(row.get("expand_ok"))

        if not expand_ok:
            out_rows.append({
                "episode_index": ep_index,
                "category": category,
                "expand_ok": False,
                "evaluation_ok": False,
                "skip_reason": row.get("skip_reason", "Expansion not available"),
            })
            continue

        review = review_by_index.get(ep_index, {})
        retrieval = retrieval_by_index.get(ep_index, {})

        episode_text = row.get("episode_text", "")
        candidate_text = row.get("candidate_text", "")
        context_text = retrieval.get("context_text", "")

        status(f"Chapter {chapter_n}: Episode Evaluate {ep_index}")

        values = {
            "episode_text": episode_text,
            "candidate_text": candidate_text,
            "context_text": context_text,
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

        raw_text = _call_runner_text(
            runner=runner,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
        )

        obj = _parse_json_object(raw_text)
        obj = _validate_episode_evaluation_obj(obj)

        out_rows.append({
            "episode_index": ep_index,
            "category": category,
            "expand_ok": True,
            "evaluation_ok": True,
            "review_label": review.get("review_label"),
            "review_reason": review.get("review_reason"),
            "episode_text": episode_text,
            "candidate_text": candidate_text,
            "retrieval_best_overall": retrieval.get("best_overall"),
            "retrieval_filtered_sources": retrieval.get("filtered_sources", 0),
            "retrieval_filtered_hits": retrieval.get("filtered_hits", 0),
            "citation_count": len(retrieval.get("citations", []) or []),
            "grounded": obj["grounded"],
            "scope_creep": obj["scope_creep"],
            "merges_other_episodes": obj["merges_other_episodes"],
            "meaning_changed": obj["meaning_changed"],
            "adds_supported_detail": obj["adds_supported_detail"],
            "candidate_is_materially_better": obj["candidate_is_materially_better"],
            "recommend_accept": obj["recommend_accept"],
            "reasons": obj["reasons"],
            "supported_details": obj["supported_details"],
            "unsupported_or_risky_details": obj["unsupported_or_risky_details"],
        })

    out_path = _episode_evaluations_path(ctx, chapter_n)
    out_path.write_text(
        json.dumps(out_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts: dict[str, int] = {
        "evaluated": 0,
        "accepted": 0,
        "rejected": 0,
        "skipped": 0,
    }

    for row in out_rows:
        if not row.get("evaluation_ok"):
            counts["skipped"] += 1
            continue

        counts["evaluated"] += 1
        if row.get("recommend_accept"):
            counts["accepted"] += 1
        else:
            counts["rejected"] += 1

    logger.info("Wrote episode evaluations: %s", out_path)
    logger.info(
        "Episode evaluation counts for Chapter %d: %s",
        chapter_n,
        counts,
    )
    return out_rows

# Episode decisions
def _load_episode_evaluations(ctx: BookContext, chapter_n: int) -> list[dict[str, Any]]:
    path = _episode_evaluations_path(ctx, chapter_n)
    return json.loads(path.read_text(encoding="utf-8"))



