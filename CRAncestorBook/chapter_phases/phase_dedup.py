# phase_dedup.py

from pathlib import Path
from typing import Any
import time
import logging

from CRAncestorBook.core import BookContext, CODE_COMP_DRAFT, CODE_DUP_DETECT, CODE_DUP_COMBINE, CODE_DUP_RESOLVE
from CRAncestorBook.ai import build_runner
from CRAncestorBook.config import get_model_substep, RUN_CONFIG

from CRAncestorBook.pipeline import StepDefinition, PipelineRunner

from CRAncestorBook.chapter_pipeline_runtime.step_validation import (
    verify_step_prereqs,
    GlobRequirement,
    StepPrereqs,
)

from CRAncestorBook.paths import chapter_output, chapter_payload, chapter_glob, chapter_path, global_payload, global_output

from WrapEmit import status, error, info, complete

logger = logging.getLogger(__name__)

# Derived artifact (not a StepDefinition): per-chapter slice of the global ledger used as input to CODE_DUP_RESOLVE.
_DERIVED_DUPLICATE_ACTION_LEDGER = "duplicate_action_ledger_for_chapter"

PHASE_DEDUP_PREREQS = StepPrereqs(
    required_dirs=("Chapters", "Ledger"),
    required_globs=(
        GlobRequirement(
            pattern=chapter_glob(CODE_COMP_DRAFT),
            missing_msg=(
                f"Missing Phase Deduplication inputs: no {chapter_glob(CODE_COMP_DRAFT)} files found.\n"
                "Run Completeness Draft first, or confirm your Completeness Draft output path."
            ),
        ),
    ),
)

# Step Duplicate workflow:
#   A) per-chapter adjacent duplicate detection (N vs N-1/N+1)
#   B) global combine to action ledger
#   C) per-chapter resolution (apply ledger to Chapter N only)
STEPS: list[StepDefinition] = [
    StepDefinition(
        code=CODE_DUP_DETECT,
        name="Duplicate Detection (Adjacency)",
        prompt_name="chapter_duplicate_detection",
        output_relpath_pattern=chapter_output(CODE_DUP_DETECT),
        payload_relpath_pattern=chapter_payload(CODE_DUP_DETECT),
    ),
    StepDefinition(
        code=CODE_DUP_COMBINE,
        name="Duplicate Combine (Global Ledger)",
        prompt_name="chapter_duplicates_combine",
        output_relpath_pattern=global_output(CODE_DUP_COMBINE),
        payload_relpath_pattern=global_payload(CODE_DUP_COMBINE),
    ),
    StepDefinition(
        code=CODE_DUP_RESOLVE,
        name="Duplicate Resolution (Apply Ledger)",
        prompt_name="chapter_duplicate_resolution",
        output_relpath_pattern=chapter_output(CODE_DUP_RESOLVE),
        payload_relpath_pattern=chapter_payload(CODE_DUP_RESOLVE),
    ),
]

def inputs_for_step(step_code: str, ctx: BookContext, chapter_n: int) -> list[Path]:
    root = ctx.root

    if step_code == CODE_DUP_DETECT:
        prev_path, next_path = _neighbor_paths(ctx, chapter_n)
        return [
            _chapter_text_for_dedup(root, chapter_n),
            prev_path,
            next_path,
        ]

    if step_code == CODE_DUP_COMBINE:
        # Global step: inputs are whatever detection reports exist (stable list built at runtime)
        # Chapter list is injected via values_for_step; prompt files come from %m% list placeholder.
        # Combine consumes the per-chapter detection outputs (or empties created as fail-safe)
        reports: list[Path] = []

        for n in sorted(ctx.chapters):
            p = chapter_path(root, n, CODE_DUP_DETECT)
            if p.exists():
                reports.append(p)
        return reports

    if step_code == CODE_DUP_RESOLVE:
        return [
            _ledger_for_chapter(root, chapter_n),
            _chapter_text_for_dedup(root, chapter_n),
        ]

    raise ValueError(f"Unknown step code: {step_code}")

def values_for_step(ctx: BookContext, chapter_n: int, step: StepDefinition) -> dict[str, Any]:
    root = ctx.root

    # GLOBAL step: must not call ctx.chapter(chapter_n) because combine is invoked with chapter_n=0
    if step.code == CODE_DUP_COMBINE:
        reports: list[Path] = []
        for n in sorted(ctx.chapters):
            p = chapter_path(root, n, CODE_DUP_DETECT)
            if p.exists():
                reports.append(p)

        return {
            "chapter_list": ctx.chapter_list_text,
            "detection_reports": reports,  # %m% detection_reports %m%
        }

    # Per-chapter steps only (chapter_n is valid here)
    ch = ctx.chapter(chapter_n)

    values: dict[str, Any] = {
        "chapter_title": getattr(ch, "title", ""),
        "chapter_dates": getattr(ch, "date_range", getattr(ch, "dates", "")),
    }

    if step.code == CODE_DUP_DETECT:
        prev_n = chapter_n - 1
        next_n = chapter_n + 1

        prev_ch = ctx.chapter(prev_n) if prev_n in ctx.chapters else None
        next_ch = ctx.chapter(next_n) if next_n in ctx.chapters else None

        prev_path, next_path = _neighbor_paths(ctx, chapter_n)

        values.update({
            "prev_chapter_title": getattr(prev_ch, "title", "") if prev_ch else "",
            "prev_chapter_dates": getattr(prev_ch, "date_range", getattr(prev_ch, "dates", "")) if prev_ch else "",
            "next_chapter_title": getattr(next_ch, "title", "") if next_ch else "",
            "next_chapter_dates": getattr(next_ch, "date_range", getattr(next_ch, "dates", "")) if next_ch else "",

            # File placeholders expected by the prompt
            "chapter_n_text": _chapter_text_for_dedup(root, chapter_n),
            "chapter_n_minus_1_text": prev_path,
            "chapter_n_plus_1_text": next_path,
        })
        return values

    if step.code == CODE_DUP_RESOLVE:
        prev_n = chapter_n - 1
        next_n = chapter_n + 1

        prev_ch = ctx.chapter(prev_n) if prev_n in ctx.chapters else None
        next_ch = ctx.chapter(next_n) if next_n in ctx.chapters else None

        values.update({
            "prev_chapter_title": getattr(prev_ch, "title", "") if prev_ch else "",
            "prev_chapter_dates": getattr(prev_ch, "date_range", getattr(prev_ch, "dates", "")) if prev_ch else "",
            "next_chapter_title": getattr(next_ch, "title", "") if next_ch else "",
            "next_chapter_dates": getattr(next_ch, "date_range", getattr(next_ch, "dates", "")) if next_ch else "",

            # File placeholders expected by the resolution prompt
            "duplicate_action_ledger_for_chapter": _ledger_for_chapter(root, chapter_n),
            "chapter_text_post_dedup_input": _chapter_text_for_dedup(root, chapter_n),

        })
        return values

    raise ValueError(f"Unknown step code: {step.code}")

# Module specific helpers
def _chapter_text_for_dedup(root: Path, chapter_n: int) -> Path:
    return chapter_path(root, chapter_n, CODE_COMP_DRAFT)

def _ledger_for_chapter(root: Path, chapter_n: int) -> Path:
    """
    Create a per-chapter slice of the combined ledger to prevent cross-chapter misapplication.
    Only APPROVED items for this chapter are included.
    """
    src = root / global_output(CODE_DUP_COMBINE)
    # dst = root / "Chapters" / f"Chapter_{chapter_n}" / "duplicate_action_ledger_for_chapter.txt"
    dst = chapter_path(root, chapter_n, _DERIVED_DUPLICATE_ACTION_LEDGER)

    dst.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Ledger slice src={src} exists={src.exists()}")
    logger.info(f"Ledger slice src={dst} exists={dst.exists()}")

    if not src.exists():
        dst.write_text("", encoding="utf-8")
        return dst

    keep: list[str] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        # Ledger lines look like: EVT=... |CH=Chapter 1| ... |STATUS=APPROVED|
        # if f"|CH=Chapter {chapter_n}|" in line and "|STATUS=APPROVED|" in line:
        #     keep.append(line)
        ch_a = f"|CH={chapter_n}|"
        ch_b = f"|CH=Chapter {chapter_n}|"
        if (ch_a in line or ch_b in line) and "|STATUS=APPROVED|" in line:
            keep.append(line)

    dst.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
    return dst

def _empty_neighbor_file(root: Path, *, chapter_n: int, which: str) -> Path:
    """
    Create deterministic empty placeholder files so:
    - the prompt always receives a file for N-1 and/or N+1
    - the debug payload file list is stable/auditable
    """
    p = root / "Chapters" / f"Chapter_{chapter_n}" / f"_EMPTY_{which}.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("", encoding="utf-8")
    return p

def _neighbor_paths(ctx: BookContext, chapter_n: int) -> tuple[Path, Path]:
    """
    Returns (prev_text_path, next_text_path) for prompt placeholders.
    Missing neighbors are represented by an empty file (not an error).
    """
    root = ctx.root
    prev_n = chapter_n - 1
    next_n = chapter_n + 1

    prev_candidate = _chapter_text_for_dedup(root, prev_n)
    if prev_n in ctx.chapters  and prev_candidate.exists():
        prev_path = prev_candidate
    else:
        prev_path = _empty_neighbor_file(root, chapter_n=chapter_n, which="PREV")

    next_candidate = _chapter_text_for_dedup(root, next_n)
    if next_n in ctx.chapters and next_candidate.exists():
        next_path = next_candidate
    else:
        next_path = _empty_neighbor_file(root, chapter_n=chapter_n, which="NEXT")

    return prev_path, next_path

def _touch_empty_report_if_missing(root: Path, chapter_n: int) -> None:
    """
    If detection fails, we still want combine to be able to run (per your rule).
    We create an empty report as a fail-safe audit artifact.
    """
    p = chapter_path(root, chapter_n, CODE_DUP_DETECT)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("", encoding="utf-8")

# Runstep
def run_phase_dedup(ctx: BookContext, *, chapters: list[int], prompt_lib: Any) -> None:
    # ok, msg = verify_step4_prereqs(ctx.root)
    # if not ok:
    #     error(msg)
    #     return

    ok, msg = verify_step_prereqs(ctx.root, PHASE_DEDUP_PREREQS)
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

    def runner_for(step_code: str):
        ai_model = get_model_substep(step_code)
        logger.info("AI Model (%s): %s", step_code, ai_model)
        return build_runner(ai_model=ai_model)

    # A) Per-chapter detection
    detect_step = next(s for s in STEPS if s.code == CODE_DUP_DETECT)
    for chapter_n in chapters:
        status(f"Chapter {chapter_n}")

        chapter_input = _chapter_text_for_dedup(ctx.root, chapter_n)
        if not chapter_input.exists() or chapter_input.stat().st_size == 0:
            error(
                f"Skipping {detect_step.name} for Chapter {chapter_n}: "
                f"missing or empty input file: {chapter_input}"
            )
            _touch_empty_report_if_missing(ctx.root, chapter_n)
            continue

        inputs = inputs_for_step(detect_step.code, ctx, chapter_n)
        output_path = ctx.root / detect_step.output_relpath_pattern.format(N=chapter_n)
        payload_path = ctx.root / detect_step.payload_relpath_pattern.format(N=chapter_n)

        info(
            "\n".join([
                f"Chapter {chapter_n} — {detect_step.name}",
                f"Step code : {detect_step.code}",
                f"Inputs    : {len(inputs)} files",
                *[f"  - {p}" for p in inputs],
                f"Output    : {output_path}",
                f"Payload   : {payload_path}"
            ])
        )

        ok = core.run_one_step(
            detect_step,
            ctx=ctx,
            chapter_n=chapter_n,
            runner=runner_for(detect_step.code),
            prompt_lib=prompt_lib,
            inputs_for_step=inputs_for_step,
            values_for_step=values_for_step,
        )
        if ok:
            info(f"✓ Completed: {detect_step.name}")
        else:
            error(f"✗ Failed: {detect_step.name} (Chapter {chapter_n}) — continuing (combine must still run)")
            _touch_empty_report_if_missing(ctx.root, chapter_n)

        if RUN_CONFIG.chapter_delay_seconds > 0:
            status(f"Waiting {RUN_CONFIG.chapter_delay_seconds}s before next chapter...")
            time.sleep(RUN_CONFIG.chapter_delay_seconds)

    # B) Global combine (always runs)
    combine_step = next(s for s in STEPS if s.code == CODE_DUP_COMBINE)
    status("Global duplicate combine")
    combine_inputs = inputs_for_step(combine_step.code, ctx, chapter_n=0)
    combine_output = ctx.root / combine_step.output_relpath_pattern.format(N=0)
    payload_path = ctx.root / combine_step.payload_relpath_pattern.format(N=0)

    info(
        "\n".join([
            f"{combine_step.name}",
            f"Step code : {combine_step.code}",
            f"Inputs    : {len(combine_inputs)} files",
            *[f"  - {p}" for p in combine_inputs],
            f"Output    : {combine_output}",
            f"Payload   : {payload_path}"
        ])
    )

    # if not combine_inputs:
    #     error("Skipping Duplicate Combine: no duplicate detection reports were generated.")
    #     complete("Dedup complete (no combine inputs).")
    #     return

    ok = core.run_one_step(
        combine_step,
        ctx=ctx,
        chapter_n=0,
        runner=runner_for(combine_step.code),
        prompt_lib=prompt_lib,
        inputs_for_step=inputs_for_step,
        values_for_step=values_for_step,
        # ensure_output_dirs_for_step=ensure_output_dirs_for_step,
    )
    if ok:
        info(f"✓ Completed: {combine_step.name}")
    else:
        error(f"✗ Failed: {combine_step.name} — skipping resolution")
        complete("Step 4 complete (combine failed).")
        return

    if RUN_CONFIG.step_delay_seconds > 0:
        status(f"Waiting {RUN_CONFIG.step_delay_seconds}s before next step...")
        time.sleep(RUN_CONFIG.step_delay_seconds)

    # C) Per-chapter resolution (apply ledger to Chapter N only)
    resolve_step = next(s for s in STEPS if s.code == CODE_DUP_RESOLVE)
    for chapter_n in chapters:
        status(f"Chapter {chapter_n}")

        inputs = inputs_for_step(resolve_step.code, ctx, chapter_n)
        output_path = ctx.root / resolve_step.output_relpath_pattern.format(N=chapter_n)
        payload_path = ctx.root / resolve_step.payload_relpath_pattern.format(N=chapter_n)

        info(
            "\n".join([
                f"Chapter {chapter_n} — {resolve_step.name}",
                f"Step code : {resolve_step.code}",
                f"Inputs    : {len(inputs)} files",
                *[f"  - {p}" for p in inputs],
                f"Output    : {output_path}",
                f"Payload   : {payload_path}"
            ])
        )

        ok = core.run_one_step(
            resolve_step,
            ctx=ctx,
            chapter_n=chapter_n,
            runner=runner_for(resolve_step.code),
            prompt_lib=prompt_lib,
            inputs_for_step=inputs_for_step,
            values_for_step=values_for_step,
        )
        if ok:
            info(f"✓ Completed: {resolve_step.name}")
        else:
            error(f"✗ Failed: {resolve_step.name} (Chapter {chapter_n}) — continuing")

        if RUN_CONFIG.step_delay_seconds > 0:
            status(f"Waiting {RUN_CONFIG.step_delay_seconds}s before next step...")
            time.sleep(RUN_CONFIG.step_delay_seconds)

    complete("Step 4 complete.")
