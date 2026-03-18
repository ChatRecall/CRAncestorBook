# phase_draft.py

from pathlib import Path
from typing import Any
import logging

from CRAncestorBook.core import BookContext, CODE_INITIAL_DRAFT
from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import get_model_substep, RUN_CONFIG

from CRAncestorBook.pipeline import StepDefinition, PipelineRunner

from CRAncestorBook.chapter_pipeline_runtime.step_validation import (
    verify_step_prereqs,
    StepPrereqs,
)

from CRAncestorBook.paths import chapter_output, chapter_payload

from WrapEmit import status, error, info, complete

logger = logging.getLogger(__name__)

PHASE_DRAFT_PREREQS = StepPrereqs(
    required_dirs=("Sources/primary", "Sources/secondary", "Sources/official"),
)

# Initial chapter draft (one prompt per chapter)
STEPS: list[StepDefinition] = [
    StepDefinition(
        code=CODE_INITIAL_DRAFT,
        name="Initial Chapter Draft",
        prompt_name="chapter_initial_draft",
        output_relpath_pattern=chapter_output(CODE_INITIAL_DRAFT),
        payload_relpath_pattern= chapter_payload(CODE_INITIAL_DRAFT),
    )
]


def inputs_for_step(step_code: str, ctx: BookContext, chapter_n: int) -> list[Path]:
    if step_code == CODE_INITIAL_DRAFT:
        return ctx.all_sources

    raise ValueError(f"Unknown step code: {step_code}")

def values_for_step(ctx: BookContext, chapter_n: int, step: StepDefinition) -> dict[str, Any]:
    return {
        "all_sources": ctx.all_sources,
        "primary_sources": ctx.primary_sources,
        "secondary_sources": ctx.secondary_sources,
        "official_sources": ctx.official_sources,
        "chapter_list": ctx.chapter_list_text,
        "chapter": ctx.chapter(chapter_n).scope_text,
    }

def run_phase_draft(ctx: BookContext, *, chapters: list[int], prompt_lib: Any) -> None:
    ok, msg = verify_step_prereqs(ctx.root, PHASE_DRAFT_PREREQS)
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

    for chapter_n in chapters:
        status(f"Chapter {chapter_n}")

        ai_model = get_model_substep(CODE_INITIAL_DRAFT)
        runner = build_runner(ai_model=ai_model)
        logger.info("AI Model: %s", ai_model)

        # Phase Draft is currently one step (initial_draft)
        step = STEPS[0]

        inputs = inputs_for_step(step.code, ctx, chapter_n)
        output_path = ctx.root / step.output_relpath_pattern.format(N=chapter_n)
        payload_path = ctx.root / step.payload_relpath_pattern.format(N=chapter_n)

        info(
            "\n".join([
                f"Chapter {chapter_n} — {step.name}",
                f"Step code : {step.code}",
                f"Inputs    : {len(inputs)} files",
                *[f"  - {p}" for p in inputs],
                f"Output    : {output_path}",
                f"Payload   : {payload_path}",
            ])
        )

        ok = core.run_one_step(
            step,
            ctx=ctx,
            chapter_n=chapter_n,
            runner=runner,
            prompt_lib=prompt_lib,
            inputs_for_step=inputs_for_step,
            values_for_step=values_for_step,
            # ensure_output_dirs_for_step=ensure_output_dirs_for_step,
        )
        if not ok:
            error(f"Stopping Initial Draft for remaining chapters after failure in {step.name}")
            break

    complete("Initial Draft complete.")


