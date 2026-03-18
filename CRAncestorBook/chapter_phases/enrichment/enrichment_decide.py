# phases/enrichment/enrichment_decide.py

import json
from typing import Any
import logging

from CRAncestorBook.core import BookContext
from .enrichment_decompose import _load_episode_index
from .enrichment_evaluate import _load_episode_evaluations
from .enrichment_paths import _episode_decisions_path

logger = logging.getLogger(__name__)

def _run_episode_decisions(
    ctx: BookContext,
    chapter_n: int,
) -> list[dict[str, Any]]:
    episodes = _load_episode_index(ctx, chapter_n)
    eval_rows = _load_episode_evaluations(ctx, chapter_n)

    eval_by_index = {
        row["episode_index"]: row
        for row in eval_rows
    }

    out_rows: list[dict[str, Any]] = []

    for ep in episodes:
        ep_index = ep["episode_index"]
        category = ep["category"]
        original_text = ep["text"]

        ev = eval_by_index.get(ep_index)

        if not ev or not ev.get("evaluation_ok", False):
            out_rows.append({
                "episode_index": ep_index,
                "category": category,
                "decision": "keep_original",
                "decision_reason": (
                    ev.get("skip_reason", "No evaluation row found")
                    if ev else "No evaluation row found"
                ),
                "final_text": original_text,
                "source": "original",
            })
            continue

        if ev.get("recommend_accept", False):
            candidate_text = ev.get("candidate_text", "") or ""
            if not candidate_text.strip():
                out_rows.append({
                    "episode_index": ep_index,
                    "category": category,
                    "decision": "keep_original",
                    "decision_reason": "Evaluation accepted candidate, but candidate_text was empty",
                    "final_text": original_text,
                    "source": "original",
                })
            else:
                out_rows.append({
                    "episode_index": ep_index,
                    "category": category,
                    "decision": "accept_candidate",
                    "decision_reason": "; ".join(ev.get("reasons", [])) or "Accepted by evaluator",
                    "final_text": candidate_text,
                    "source": "candidate",
                })
        else:
            out_rows.append({
                "episode_index": ep_index,
                "category": category,
                "decision": "keep_original",
                "decision_reason": "; ".join(ev.get("reasons", [])) or "Evaluator did not recommend acceptance",
                "final_text": original_text,
                "source": "original",
            })

    out_path = _episode_decisions_path(ctx, chapter_n)
    out_path.write_text(
        json.dumps(out_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts: dict[str, int] = {}
    for row in out_rows:
        d = row["decision"]
        counts[d] = counts.get(d, 0) + 1

    logger.info("Wrote episode decisions: %s", out_path)
    logger.info(
        "Episode decision counts for Chapter %d: %s",
        chapter_n,
        counts,
    )
    return out_rows

