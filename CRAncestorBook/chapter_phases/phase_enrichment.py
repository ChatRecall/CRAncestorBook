# phases/phase_enrichment.py

"""
Episode-level enrichment phase.

This phase expands selected narrative episodes using supporting evidence from
the full book source pool while preserving chronology and chapter structure.

Pipeline model:
- Episode decomposition runs through the generic StepDefinition runner.
- All subsequent stages are orchestrated explicitly in Python.

Reason:
Later steps operate per-episode and depend on intermediate artifacts
(episode_index, eligibility, retrieval, review, expansions, evaluations),
so forcing them into the generic runner abstraction would make the flow less clear.

Key rule:
AI proposes changes; Python decides whether to accept them.
"""

import logging
import time
from pathlib import Path
from typing import Any

from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import RUN_CONFIG, get_model_substep
from CRAncestorBook.core import (
    BookContext,
    CODE_STYLE_POLISH,
    CODE_EPISODE_DECOMPOSE,
    CODE_EPISODE_EVALUATE,
)
from CRAncestorBook.paths import chapter_glob, chapter_output, chapter_path, chapter_payload
from CRAncestorBook.chapter_phases.enrichment.enrichment_db import _open_or_build_enrichment_db, _log_enrichment_db_summary
from CRAncestorBook.chapter_phases.enrichment.enrichment_decide import _run_episode_decisions
from CRAncestorBook.chapter_phases.enrichment.enrichment_decompose import _parse_and_write_episode_index, _write_episode_eligibility
from CRAncestorBook.chapter_phases.enrichment.enrichment_evaluate import _run_episode_evaluations
from CRAncestorBook.chapter_phases.enrichment.enrichment_expand import _run_episode_expansions
from CRAncestorBook.chapter_phases.enrichment.enrichment_paths import _phase_style_final_input_path, _episode_expansions_path
from CRAncestorBook.chapter_phases.enrichment.enrichment_reassemble import _run_episode_reassembly
from CRAncestorBook.chapter_phases.enrichment.enrichment_retrieval import _run_episode_retrieval
from CRAncestorBook.chapter_phases.enrichment.enrichment_review import _run_episode_retrieval_review
from CRAncestorBook.pipeline import PipelineRunner, StepDefinition
from CRAncestorBook.chapter_pipeline_runtime.step_validation import (
    GlobRequirement,
    StepPrereqs,
    verify_step_prereqs,
)

from WrapEmit import complete, error, info, status

logger = logging.getLogger(__name__)

PHASE_ENRICHMENT_PREREQS = StepPrereqs(
    required_dirs=("Chapters",),
    required_globs=(
        GlobRequirement(
            pattern=chapter_glob(CODE_STYLE_POLISH),
            missing_msg=(
                f"Missing Phase Enrichment inputs: no {chapter_glob(CODE_STYLE_POLISH)} files found.\n"
                "Run Style Polish first, or confirm your Style Polish output path."
            ),
        ),
    ),
)

STEPS: list[StepDefinition] = [
    StepDefinition(
        code=CODE_EPISODE_DECOMPOSE,
        name="Episode Decompose",
        prompt_name="chapter_episode_decompose",
        output_relpath_pattern=chapter_output(CODE_EPISODE_DECOMPOSE),
        payload_relpath_pattern=chapter_payload(CODE_EPISODE_DECOMPOSE),
    ),
]

def inputs_for_step(step_code: str, ctx: BookContext, chapter_n: int) -> list[Path]:
    if step_code == CODE_EPISODE_DECOMPOSE:
        return [_phase_style_final_input_path(ctx, chapter_n)]

    if step_code == CODE_EPISODE_EVALUATE:
        return [_episode_expansions_path(ctx, chapter_n)]

    raise ValueError(f"Unknown step code: {step_code}")

def values_for_step(ctx: BookContext, chapter_n: int, step: StepDefinition) -> dict[str, Any]:
    chapter = ctx.chapter(chapter_n)
    chapter_examples = "\n".join(f"- {x}" for x in chapter.examples)

    if step.code == CODE_EPISODE_DECOMPOSE:
        return {
            "chapter_text": _phase_style_final_input_path(ctx, chapter_n),
        }

    raise ValueError(f"Unknown step code: {step.code}")

def _run_episode_decompose_with_retry(
    core: PipelineRunner,
    *,
    ctx: BookContext,
    chapter_n: int,
    step: StepDefinition,
    prompt_lib: Any,
    max_attempts: int = RUN_CONFIG.max_step_retries,
    retry_delay_seconds: int = RUN_CONFIG.error_delay_seconds,
) -> bool:
    for attempt in range(1, max_attempts + 1):
        ai_model = get_model_substep(CODE_EPISODE_DECOMPOSE)
        runner = build_runner(ai_model=ai_model)
        logger.info("AI Model: %s", ai_model)
        logger.info(
            "Episode decompose attempt %d/%d for Chapter %d",
            attempt,
            max_attempts,
            chapter_n,
        )

        ok = core.run_one_step(
            step,
            ctx=ctx,
            chapter_n=chapter_n,
            runner=runner,
            prompt_lib=prompt_lib,
            inputs_for_step=inputs_for_step,
            values_for_step=values_for_step,
        )
        if not ok:
            logger.warning(
                "Episode decompose step returned False on attempt %d/%d for Chapter %d",
                attempt,
                max_attempts,
                chapter_n,
            )
        else:
            out_path = chapter_path(ctx.root, chapter_n, CODE_EPISODE_DECOMPOSE)
            text = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
            logger.info(
                "Episode decompose output chars for Chapter %d attempt %d: %d",
                chapter_n,
                attempt,
                len(text),
            )

            if text.strip():
                preview = text[:200].replace("\n", "\\n")
                logger.debug("Episode decompose preview: %s", preview)
                return True

            logger.warning(
                "Episode decompose output was empty on attempt %d/%d for Chapter %d",
                attempt,
                max_attempts,
                chapter_n,
            )

        if attempt < max_attempts:
            logger.info("Retrying episode_decompose after %s seconds...", retry_delay_seconds)
            time.sleep(retry_delay_seconds)

    return False


    # Enrichment phase structure:
    # Only the episode decomposition runs through the generic StepDefinition runner.
    # The remaining steps (retrieval, review, expansion, evaluation, decision, reassembly)
    # are executed explicitly in Python because they operate per-episode and depend on
    # intermediate artifacts produced during the phase.
    # Read full details in phases/enrichment/README.md


def run_phase_enrichment(ctx: BookContext, *, chapters: list[int], prompt_lib: Any) -> None:
    ok, msg = verify_step_prereqs(ctx.root, PHASE_ENRICHMENT_PREREQS)
    if not ok:
        error(msg)
        return

    core = PipelineRunner(
        step_delay_seconds=RUN_CONFIG.step_delay_seconds,
        max_step_retries=RUN_CONFIG.max_step_retries,
        error_delay_seconds=RUN_CONFIG.error_delay_seconds,
        retriable_statuses=RUN_CONFIG.retriable_statuses,
        wait_before_first_call=RUN_CONFIG.wait_before_first_call,
    )

    try:
        enrichment_embedder = _open_or_build_enrichment_db(ctx)
        _log_enrichment_db_summary(ctx)
        logger.info("Enrichment vector DB ready.")
    except Exception as exc:
        error(f"Failed to open/build enrichment vector DB: {exc}")
        return

    # step = next(s for s in STEPS if s.code == CODE_EPISODE_DECOMPOSE)
    step = STEPS[0]

    for chapter_n in chapters:
        status(f"Chapter {chapter_n}: Episode Decompose")

        inputs = inputs_for_step(step.code, ctx, chapter_n)
        input_path = inputs[0]
        output_path = ctx.root / step.output_relpath_pattern.format(N=chapter_n)
        payload_path = ctx.root / step.payload_relpath_pattern.format(N=chapter_n)

        info(
            "\n".join([
                f"Chapter {chapter_n} — {step.name}",
                f"Step code : {step.code}",
                f"Input     : {input_path}",
                f"Output    : {output_path}",
                f"Payload   : {payload_path}",
            ])
        )

        if not input_path.exists():
            error(f"Missing input for episode_decompose: {input_path}")
            error("Update _phase_style_final_input_path() to point at your style-polish output.")
            break

        ok = _run_episode_decompose_with_retry(
            core,
            ctx=ctx,
            chapter_n=chapter_n,
            step=step,
            prompt_lib=prompt_lib,
        )
        if not ok:
            error(f"Stopping Enrichment for remaining chapters after failure in {step.name}")
            break

        try:
            episodes = _parse_and_write_episode_index(ctx, chapter_n)
            eligibility = _write_episode_eligibility(ctx, chapter_n, episodes)

            if not any(row["eligible"] for row in eligibility):
                info(f"Chapter {chapter_n}: no eligible episodes for enrichment; skipping.")
                continue

            _run_episode_retrieval(
                ctx,
                chapter_n,
                embedder=enrichment_embedder,
            )
            _run_episode_retrieval_review(ctx, chapter_n)
            _run_episode_expansions(
                ctx,
                chapter_n,
                prompt_lib=prompt_lib,
            )
            _run_episode_evaluations(
                ctx,
                chapter_n,
                prompt_lib=prompt_lib,
            )
            _run_episode_decisions(ctx, chapter_n)
            _run_episode_reassembly(ctx, chapter_n)
        except Exception as exc:
            error(f"Failed during enrichment post-processing for Chapter {chapter_n}: {exc}")
            break

    complete("Episode decomposition complete.")

# Notes
# accept = (
#     evaluation.get("recommend_accept") is True
#     and evaluation.get("grounded") is True
#     and evaluation.get("scope_creep") is False
#     and evaluation.get("merges_other_episodes") is False
#     and evaluation.get("meaning_changed") is False
# )
