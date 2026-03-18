# phase_paragraph.py
# Paragraph Polish

from pathlib import Path
from typing import Any
import logging

from CRAncestorBook.core import (
    BookContext,
    EPISODE_REASSEMBLED_STEM,
    CODE_PARAGRAPH_POLISH
)
from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import get_model_substep, RUN_CONFIG

from CRAncestorBook.pipeline import StepDefinition, PipelineRunner

from CRAncestorBook.chapter_pipeline_runtime.step_validation import (
    verify_step_prereqs,
    GlobRequirement,
    StepPrereqs,
)

from CRAncestorBook.paths import chapter_output, chapter_payload, chapter_glob, chapter_path

from WrapEmit import status, error, info, complete

logger = logging.getLogger(__name__)

PHASE_PARAGRAPH_PREREQS = StepPrereqs(
    required_dirs=("Chapters",),
    required_globs=(
        GlobRequirement(
            pattern=chapter_glob(EPISODE_REASSEMBLED_STEM),
            missing_msg=(
                f"Missing Phase Paragraph inputs: no {chapter_glob(EPISODE_REASSEMBLED_STEM)} files found.\n"
                "Run Enrichment first, or confirm your episode reassembled output path."
            ),
        ),
    ),
)

# Step Paragraph Polish (one prompt per chapter)
STEPS: list[StepDefinition] = [
    StepDefinition(
        code=CODE_PARAGRAPH_POLISH,
        name="Paragraph Polish",
        prompt_name="chapter_paragraph_polish",
        output_relpath_pattern=chapter_output(CODE_PARAGRAPH_POLISH, ext=".md"),
        payload_relpath_pattern=chapter_payload(CODE_PARAGRAPH_POLISH),
    )
]

def _phase_enrichment_final_input_path(ctx: BookContext, chapter_n: int) -> Path:
    root = ctx.root
    return chapter_path(root, chapter_n, EPISODE_REASSEMBLED_STEM)


def inputs_for_step(step_code: str, ctx: BookContext, chapter_n: int) -> list[Path]:
    if step_code == CODE_PARAGRAPH_POLISH:
        return [_phase_enrichment_final_input_path(ctx, chapter_n)]
    raise ValueError(f"Unknown step code: {step_code}")

def values_for_step(ctx: BookContext, chapter_n: int, step: StepDefinition) -> dict[str, Any]:
    # Placeholder used by chapter_paragraph_polish prompt:
    # - %% chapter_text %%
    return {
        "chapter_text":  _phase_enrichment_final_input_path(ctx, chapter_n),
    }

def run_phase_paragraph(ctx: BookContext, *, chapters: list[int], prompt_lib: Any) -> None:
    ok, msg = verify_step_prereqs(ctx.root, PHASE_PARAGRAPH_PREREQS)
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

        ai_model = get_model_substep(CODE_PARAGRAPH_POLISH)
        runner = build_runner(ai_model=ai_model)
        logger.info("AI Model: %s", ai_model)

        step = STEPS[0]

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
            error(f"Missing input for paragraph polish: {input_path}")
            error("Update _phase_enrichment_final_input_path() to point at your episode-reassembled output.")
            break

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
            error(f"Stopping Paragraph Polish for remaining chapters after failure in {step.name}")
            break

    complete("Paragraph Polish complete.")


