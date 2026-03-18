# pipeline/runner.py
from pathlib import Path
from typing import Any, Callable, Sequence
from datetime import datetime
import time
import requests
import logging

from .definitions import StepDefinition

logger = logging.getLogger(__name__)

InputsFn = Callable[[str, Any, int], list[Path]]
ValuesFn = Callable[[Any, int, StepDefinition], dict[str, Any]]
EnsureDirsFn = Callable[[str, Path], None]


class PipelineRunner:
    def __init__(
        self,
        *,
        use_streaming: bool = True,
        step_delay_seconds: int,
        max_step_retries: int,
        error_delay_seconds: int,
        retriable_statuses: set[int],
        wait_before_first_call: bool,
    ) -> None:
        self.use_streaming = use_streaming
        self.step_delay_seconds = step_delay_seconds
        self.max_step_retries = max_step_retries
        self.error_delay_seconds = error_delay_seconds
        self.retriable_statuses = set(retriable_statuses)
        self.wait_before_first_call = wait_before_first_call

    @staticmethod
    def write_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    @staticmethod
    def missing_inputs(input_paths: Sequence[Path]) -> list[Path]:
        return [p for p in input_paths if not p.exists()]

    @staticmethod
    def render_prompt_from_library(
        *,
        prompt_lib: Any,
        step: StepDefinition,
        values: dict[str, Any],
    ) -> tuple[str, str | None, dict[str, Any]]:
        prompt_t, system_prompt = prompt_lib.get_prompt_with_system_prompt(step.prompt_name)

        raw_text = prompt_t.prompt_text
        filled_text = prompt_t.fill_placeholders(values, prompt_text=raw_text)

        # prompt_t.prompt_text = filled_text
        # rendered_user_prompt = prompt_t.get_display_prompt()

        rendered_user_prompt = filled_text

        attrs = prompt_t.default_attributes.to_dict()
        return rendered_user_prompt, system_prompt, attrs

    @staticmethod
    def build_payload(rendered_user_prompt: str, input_paths: Sequence[Path]) -> str:
        files_list = "\n".join(f"- {p.name}" for p in input_paths)
        return (
            rendered_user_prompt.rstrip()
            + "\n\nFILES PROVIDED (debug list only)\n"
            + files_list
            + "\n"
        )

    @staticmethod
    def planned_output_path(step: StepDefinition, root: Path, chapter_n: int) -> Path:
        return root / step.output_relpath_pattern.format(N=chapter_n)

    @staticmethod
    def planned_payload_path(step: StepDefinition, root: Path, chapter_n: int) -> Path:
        return root / step.payload_relpath_pattern.format(N=chapter_n)

    @staticmethod
    def print_step_summary(
        *,
        chapter_n: int,
        step: StepDefinition,
        input_paths: Sequence[Path],
        output_path: Path,
        payload_chars: int,
    ) -> None:

        logger.debug(f"Chapter {chapter_n} | Step {step.code} — {step.name}")
        for p in input_paths:
            logger.debug(f"  - {p}")
        logger.info(f"Planned output: {output_path}")
        logger.info(f"Payload chars: {payload_chars}")

    def run_one_step(
        self,
        step: StepDefinition,
        *,
        ctx: Any,
        chapter_n: int,
        runner: Any,
        prompt_lib: Any,
        inputs_for_step: InputsFn,
        values_for_step: ValuesFn,
        # ensure_output_dirs_for_step: EnsureDirsFn,
    ) -> bool:
        root: Path = ctx.root

        # ensure_output_dirs_for_step(step.code, root)

        inputs = inputs_for_step(step.code, ctx, chapter_n)
        missing = self.missing_inputs(inputs)

        if missing:
            logger.debug("\n" + "-" * 72)
            logger.debug(f"Chapter {chapter_n} | Step {step.code} — {step.name}")
            logger.error("ERROR: Missing required input file(s):")
            for p in missing:
                logger.debug(f"  - {p}")
            logger.info("Skipping this step and downstream steps for this chapter.")
            return False

        out_path = self.planned_output_path(step, root, chapter_n)
        payload_path = self.planned_payload_path(step, root, chapter_n)

        values = values_for_step(ctx, chapter_n, step)
        rendered_user_prompt, system_prompt, attrs = self.render_prompt_from_library(
            prompt_lib=prompt_lib,
            step=step,
            values=values,
        )
        payload_for_model = rendered_user_prompt
        payload_for_debug = self.build_payload(rendered_user_prompt, inputs)

        runner.set_attributes(**attrs)

        self.print_step_summary(
            chapter_n=chapter_n,
            step=step,
            input_paths=inputs,
            output_path=out_path,
            payload_chars=len(payload_for_debug),
        )

        self.write_text(payload_path, payload_for_debug)
        logger.info(f"Wrote debug payload: {payload_path}")

        if self.wait_before_first_call and self.step_delay_seconds > 0:
            logger.debug(f"Waiting {self.step_delay_seconds}s before API call...")
            time.sleep(self.step_delay_seconds)

        logger.debug(f"Sending to model... (Chapter {chapter_n}, Step {step.code})")

        for attempt in range(1, self.max_step_retries + 1):
            start = datetime.now()
            try:
                # response = runner.prompt(
                #     user_prompt=payload_for_model,
                #     system_prompt=system_prompt,
                # )
                #
                # elapsed = datetime.now() - start
                # logger.info(f"Model returned. Elapsed: {elapsed}")
                #
                # self.write_text(out_path, (response.response if response else "") or "")
                # logger.info(f"Wrote model output: {out_path}")
                # return True

                # Use streaming-collect when supported to avoid idle timeouts on long prompts
                use_stream_collect = (
                    self.use_streaming
                    and callable(getattr(runner, "prompt_stream_collect", None))
                )

                if use_stream_collect:
                    logger.debug("Using runner.prompt_stream_collect()")
                    text = runner.prompt_stream_collect(
                        user_prompt=payload_for_model,
                        system_prompt=system_prompt,
                    )
                else:
                    logger.debug("Using runner.prompt() (non-streaming)")
                    response = runner.prompt(
                        user_prompt=payload_for_model,
                        system_prompt=system_prompt,
                    )
                    text = (response.response if response else "") or ""

                # elapsed = datetime.now() - start
                # logger.info(f"Model returned. Elapsed: {elapsed}")
                #
                # self.write_text(out_path, text)
                # logger.info(f"Wrote model output: {out_path}")
                # return True

                elapsed = datetime.now() - start
                # text = text or ""
                text = (text or "").strip()
                preview = text[:300].replace("\n", "\\n")

                logger.info(f"Model returned. Elapsed: {elapsed}")
                logger.info(f"Model output chars: {len(text)}")
                logger.debug(f"Model output preview: {preview}")

                # if not text.strip():
                #     logger.error(
                #         f"Empty model output for Chapter {chapter_n}, Step {step.code}. "
                #         f"Runner returned no usable text."
                #     )
                #     return False

                # Retry for empty returns
                if not text.strip():
                    if attempt >= self.max_step_retries:
                        logger.error(
                            f"Empty model output for Chapter {chapter_n}, Step {step.code} "
                            f"after {self.max_step_retries} attempts. "
                            f"Runner returned no usable text."
                        )
                        logger.error(
                            f"Giving up on Chapter {chapter_n}, Step {step.code} after "
                            f"{self.max_step_retries} attempts. Skipping remaining steps for this chapter."
                        )
                        return False

                    wait_minutes = self.error_delay_seconds / 60
                    logger.error(
                        f"Empty model output for Chapter {chapter_n}, Step {step.code} "
                        f"(attempt {attempt}/{self.max_step_retries}). "
                        f"Retrying in {wait_minutes:g} minutes..."
                    )
                    time.sleep(self.error_delay_seconds)
                    continue

                self.write_text(out_path, text)
                logger.info(f"Wrote model output: {out_path}")
                return True

            except Exception as e:
                msg = str(e)

                status_code = None
                if isinstance(e, requests.exceptions.HTTPError):
                    resp = getattr(e, "response", None)
                    status_code = resp.status_code if resp is not None else None

                # Hard-stop: not retriable, not chapter-scoped.
                if status_code == 402:
                    logger.critical(f"FATAL: API spend limit reached (HTTP 402). Error: {msg}")
                    # Raise to stop the whole pipeline (not just this chapter)
                    raise

                can_retry = (status_code in self.retriable_statuses)

                if (not can_retry) or (attempt >= self.max_step_retries):
                    logger.error(
                        f"Step failed (attempt {attempt}/{self.max_step_retries}). "
                        f"Status={status_code}. Error: {msg}"
                    )
                    logger.error(
                        f"Giving up on Chapter {chapter_n}, Step {step.code} after "
                        f"{self.max_step_retries} attempts. Skipping remaining steps for this chapter."
                    )
                    return False

                wait_minutes = self.error_delay_seconds / 60
                logger.error(
                    f"Step error (attempt {attempt}/{self.max_step_retries}). "
                    f"Status={status_code}. Retrying in {wait_minutes:g} minutes..."
                )
                time.sleep(self.error_delay_seconds)

        return False


