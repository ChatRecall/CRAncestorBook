# toc_phases/phase_toc.py

from pathlib import Path
from typing import Any
import logging

from CRAncestorBook.ai import build_runner, load_prompt_library
from CRAncestorBook.config import RUN_CONFIG, get_model_substep
from CRAncestorBook.pipeline import StepDefinition
from CRAncestorBook.pipeline.global_runner import GlobalPipelineRunner
from CRAncestorBook.paths import planning_output, planning_payload
from CRAncestorBook.toc_build.toc_context import TOCContext

from WrapEmit import complete, error, info, status

logger = logging.getLogger(__name__)


STEPS: list[StepDefinition] = [
    StepDefinition(
        code="extract_events",
        name="Extract Life Events",
        prompt_name="toc_extract_events",
        output_relpath_pattern=planning_output("toc_event_inventory.txt"),
        payload_relpath_pattern=planning_payload("extract_events"),
    ),
    StepDefinition(
        code="map_stages",
        name="Map Events to Life Stages",
        prompt_name="toc_map_stages",
        output_relpath_pattern=planning_output("toc_stage_grouped_events.txt"),
        payload_relpath_pattern=planning_payload("map_stages"),
    ),
    StepDefinition(
        code="detect_breakpoints",
        name="Detect Chapter Breakpoints",
        prompt_name="toc_detect_breakpoints",
        output_relpath_pattern=planning_output("toc_chapter_breakpoints.txt"),
        payload_relpath_pattern=planning_payload("detect_breakpoints"),
    ),
    StepDefinition(
        code="generate_chapters",
        name="Generate Draft Chapters",
        prompt_name="toc_generate_chapters",
        output_relpath_pattern=planning_output("toc_draft_chapters.txt"),
        payload_relpath_pattern=planning_payload("generate_chapters"),
    ),
    StepDefinition(
        code="generate_examples",
        name="Generate Chapter Examples",
        prompt_name="toc_generate_examples",
        output_relpath_pattern=planning_output("toc_chapter_examples.txt"),
        payload_relpath_pattern=planning_payload("generate_examples"),
    ),
    StepDefinition(
        code="generate_toml",
        name="Generate Chapters TOML",
        prompt_name="toc_generate_toml",
        output_relpath_pattern=planning_output("chapters.generated.toml"),
        payload_relpath_pattern=planning_payload("generate_toml"),
    ),
]


def get_step(code: str) -> StepDefinition:
    for step in STEPS:
        if step.code == code:
            return step
    raise KeyError(f"Unknown TOC step code: {code}")


def step_output_path(ctx: TOCContext, code: str) -> Path:
    step = get_step(code)
    return ctx.root / step.output_relpath_pattern


def inputs_for_step(step_code: str, ctx: TOCContext) -> list[Path]:
    if step_code == "extract_events":
        return ctx.all_source_files()

    if step_code == "map_stages":
        return [ctx.event_inventory_path]

    if step_code == "detect_breakpoints":
        return [ctx.stage_grouped_events_path]

    if step_code == "generate_chapters":
        return [
            ctx.stage_grouped_events_path,
            ctx.chapter_breakpoints_path,
        ]

    if step_code == "generate_examples":
        return [
            ctx.approved_chapters_path,
            ctx.event_inventory_path,
        ]

    if step_code == "generate_toml":
        return [
            ctx.approved_chapters_path,
            ctx.chapter_examples_path,
        ]

    raise KeyError(f"Unhandled TOC step code: {step_code}")


def values_for_step(ctx: TOCContext, step: StepDefinition) -> dict[str, Any]:
    if step.code == "extract_events":
        # %d% source_materials %d%
        return {
            "primary_sources": str(ctx.root / "Sources" / "primary"),
            "secondary_sources": str(ctx.root / "Sources" / "secondary"),
            "official_sources": str(ctx.root / "Sources" / "official"),
        }

    if step.code == "map_stages":
        return {
            "event_inventory": ctx.event_inventory_path.read_text(encoding="utf-8"),
        }

    if step.code == "detect_breakpoints":
        return {
            "stage_grouped_events": ctx.stage_grouped_events_path.read_text(encoding="utf-8"),
        }

    if step.code == "generate_chapters":
        return {
            "stage_grouped_events": ctx.stage_grouped_events_path.read_text(encoding="utf-8"),
            "chapter_breakpoints": ctx.chapter_breakpoints_path.read_text(encoding="utf-8"),
        }

    if step.code == "generate_examples":
        return {
            "approved_chapters": ctx.approved_chapters_path.read_text(encoding="utf-8"),
            "event_inventory": ctx.event_inventory_path.read_text(encoding="utf-8"),
        }

    if step.code == "generate_toml":
        return {
            "approved_chapters": ctx.approved_chapters_path.read_text(encoding="utf-8"),
            "chapter_examples": ctx.chapter_examples_path.read_text(encoding="utf-8"),
        }

    raise KeyError(f"Unhandled TOC step code: {step.code}")


def should_skip_step(ctx: TOCContext, step: StepDefinition, force: bool) -> bool:
    if force:
        return False
    return (ctx.root / step.output_relpath_pattern).exists()


def approval_message(ctx: TOCContext) -> str:
    return (
        "Manual approval required.\n"
        f"Review draft chapters:\n  {ctx.draft_chapters_path}\n"
        f"Save approved outline as:\n  {ctx.approved_chapters_path}\n"
        "Then rerun the TOC pipeline to continue."
    )


def resolve_step_sequence(
    *,
    start_code: str | None = None,
    stop_code: str | None = None,
) -> list[StepDefinition]:
    active = STEPS

    if start_code:
        found = False
        trimmed: list[StepDefinition] = []
        for step in active:
            if step.code == start_code:
                found = True
            if found:
                trimmed.append(step)
        if not found:
            raise KeyError(f"Unknown start_code: {start_code}")
        active = trimmed

    if stop_code:
        trimmed = []
        found = False
        for step in active:
            trimmed.append(step)
            if step.code == stop_code:
                found = True
                break
        if not found:
            raise KeyError(f"Unknown stop_code: {stop_code}")
        active = trimmed

    return active


def run_phase_toc(
    ctx: TOCContext,
    *,
    force: bool = False,
    start_code: str | None = None,
    stop_code: str | None = None,
    prompt_library_path: str | Path | None = None,
    auto_approve: bool = False,
) -> None:
    ctx.ensure_planning_dirs()

    prompt_lib = load_prompt_library(prompt_library_path)

    global_runner = GlobalPipelineRunner(
        use_streaming=RUN_CONFIG.use_streaming,
        step_delay_seconds=RUN_CONFIG.step_delay_seconds,
        max_step_retries=RUN_CONFIG.max_step_retries,
        error_delay_seconds=RUN_CONFIG.error_delay_seconds,
        retriable_statuses=set(RUN_CONFIG.retriable_statuses),
        wait_before_first_call=RUN_CONFIG.wait_before_first_call,
    )

    sequence = resolve_step_sequence(start_code=start_code, stop_code=stop_code)

    for step in sequence:
        if step.code == "generate_examples" and not ctx.approved_chapters_exists:
            if auto_approve:
                info("Auto-approving draft chapters for development.")
                ctx.approved_chapters_path.write_text(
                    ctx.draft_chapters_path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            else:
                status(approval_message(ctx))
                return

        if should_skip_step(ctx, step, force=force):
            info(f"Skipping {step.code} (output exists)")
            continue

        substep_model = get_model_substep(step.prompt_name)
        # substep_model = get_model_substep(step.code)
        runner = build_runner(ai_model=substep_model)

        status(f"Running TOC step: {step.name}")
        ok = global_runner.run_one_step(
            step,
            ctx=ctx,
            runner=runner,
            prompt_lib=prompt_lib,
            inputs_for_step=inputs_for_step,
            values_for_step=values_for_step,
        )

        if not ok:
            error(f"TOC step failed: {step.code}")
            return

        info(f"Completed TOC step: {step.code}")

        if step.code == "generate_chapters" and not ctx.approved_chapters_exists:
            if auto_approve:
                info("Auto-approving draft chapters for development.")
                ctx.approved_chapters_path.write_text(
                    ctx.draft_chapters_path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            else:
                status(approval_message(ctx))
                return

    if ctx.generated_toml_exists:
        complete(f"TOC pipeline complete: {ctx.generated_toml_path}")
    else:
        info("TOC pipeline ended before TOML generation.")

