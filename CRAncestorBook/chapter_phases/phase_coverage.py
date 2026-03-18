# phase_coverage.py

from pathlib import Path
from typing import Any
import time
import logging

from CRAncestorBook.core import BookContext, CODE_INITIAL_DRAFT, CODE_COMP_AUDIT, CODE_COMP_DRAFT
from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import get_model_substep, RUN_CONFIG

from CRAncestorBook.pipeline import StepDefinition, PipelineRunner

from CRAncestorBook.chapter_pipeline_runtime.step_validation import (
    verify_step_prereqs,
    GlobRequirement,
    StepPrereqs,
)


from CRAncestorBook.paths import chapter_output, chapter_payload, chapter_glob, chapter_path

from WrapEmit import status, progress, error, info, complete

logger = logging.getLogger(__name__)

PHASE_COVERAGE_PREREQS = StepPrereqs(
    required_dirs=("Chapters",),
    required_globs=(
        GlobRequirement(
            pattern=chapter_glob(CODE_INITIAL_DRAFT),
            missing_msg=(
                f"Missing Phase Coverage inputs: no {chapter_glob(CODE_INITIAL_DRAFT)} files found.\n"
                "Run Initial Chapter Draft first, or confirm your Initial Chapter Draft output path."
            ),
        ),
    ),
)

STEPS: list[StepDefinition] = [
    StepDefinition(
        code=CODE_COMP_AUDIT,
        name="Coverage Audit",
        prompt_name="chapter_coverage_audit",
        output_relpath_pattern=chapter_output(CODE_COMP_AUDIT),
        payload_relpath_pattern=chapter_payload(CODE_COMP_AUDIT)
    ),
    StepDefinition(
        code=CODE_COMP_DRAFT,
        name="Coverage Inclusion",
        prompt_name="chapter_coverage_inclusion",
        output_relpath_pattern=chapter_output(CODE_COMP_DRAFT),
        payload_relpath_pattern=chapter_payload(CODE_COMP_DRAFT)
    ),
]


def inputs_for_step(step_code: str, ctx: BookContext, chapter_n: int) -> list[Path]:
    root = ctx.root
    base_inputs = ctx.all_sources

    if step_code == CODE_COMP_AUDIT:
        return base_inputs + [chapter_path(root, chapter_n, CODE_INITIAL_DRAFT)]
    if step_code == CODE_COMP_DRAFT:
        return base_inputs + [
            chapter_path(root, chapter_n, CODE_INITIAL_DRAFT),
            chapter_path(root, chapter_n, CODE_COMP_AUDIT),
        ]

    raise ValueError(f"Unknown step code: {step_code}")

def values_for_step(ctx: BookContext, chapter_n: int, step: StepDefinition) -> dict[str, Any]:
    root = ctx.root
    values: dict[str, Any] = {
        "all_sources": ctx.all_sources,
        "primary_sources": ctx.primary_sources,
        "secondary_sources": ctx.secondary_sources,
        "official_sources": ctx.official_sources,
        "chapter_list": ctx.chapter_list_text,
        "chapter": ctx.chapter(chapter_n).scope_text,
    }

    if step.code in {CODE_COMP_AUDIT, CODE_COMP_DRAFT}:
        values["chapter_text_raw"] = chapter_path(root, chapter_n, CODE_INITIAL_DRAFT)

    if step.code == CODE_COMP_DRAFT:
        values["completeness_audit"] = chapter_path(root, chapter_n, CODE_COMP_AUDIT)

    return values

def run_phase_coverage(ctx: BookContext, *, chapters: list[int], prompt_lib: Any) -> None:
    ok, msg = verify_step_prereqs(ctx.root, PHASE_COVERAGE_PREREQS)
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

        for idx, step in enumerate(STEPS):
            ai_model = get_model_substep(step.code)
            runner = build_runner(ai_model=ai_model)
            logger.info("AI Model (%s): %s", step.code, ai_model)

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
            )
            if ok:
                info(f"✓ Completed: {step.name}")
            else:
                error(f"✗ Failed: {step.name} — skipping remaining steps")
                break

            if idx < (len(STEPS) - 1) and RUN_CONFIG.step_delay_seconds > 0:
                status(f"Waiting {RUN_CONFIG.step_delay_seconds}s before next step...")
                time.sleep(RUN_CONFIG.step_delay_seconds)

        if RUN_CONFIG.chapter_delay_seconds > 0:
            status(f"Waiting {RUN_CONFIG.chapter_delay_seconds}s before next chapter...")
            time.sleep(RUN_CONFIG.chapter_delay_seconds)

    complete("Steps complete.")
