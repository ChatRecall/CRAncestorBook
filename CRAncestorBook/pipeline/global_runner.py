# pipeline/global_runner.py

from pathlib import Path
from typing import Any, Callable, Sequence
from datetime import datetime
import time
import requests
import logging

from .definitions import StepDefinition

logger = logging.getLogger(__name__)

GlobalInputsFn = Callable[[str, Any], list[Path]]
GlobalValuesFn = Callable[[Any, StepDefinition], dict[str, Any]]


class GlobalPipelineRunner:
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
    def planned_output_path(step: StepDefinition, root: Path) -> Path:
        return root / step.output_relpath_pattern

    @staticmethod
    def planned_payload_path(step: StepDefinition, root: Path) -> Path:
        return root / step.payload_relpath_pattern

    @staticmethod
    def print_step_summary(
        *,
        step: StepDefinition,
        input_paths: Sequence[Path],
        output_path: Path,
        payload_chars: int,
    ) -> None:
        logger.debug("Step %s — %s", step.code, step.name)
        for p in input_paths:
            logger.debug("  - %s", p)
        logger.info("Planned output: %s", output_path)
        logger.info("Payload chars: %s", payload_chars)

    def run_one_step(
        self,
        step: StepDefinition,
        *,
        ctx: Any,
        runner: Any,
        prompt_lib: Any,
        inputs_for_step: GlobalInputsFn,
        values_for_step: GlobalValuesFn,
    ) -> bool:
        root: Path = ctx.root

        inputs = inputs_for_step(step.code, ctx)
        missing = self.missing_inputs(inputs)

        if missing:
            logger.debug("\n" + "-" * 72)
            logger.debug("Step %s — %s", step.code, step.name)
            logger.error("ERROR: Missing required input file(s):")
            for p in missing:
                logger.debug("  - %s", p)
            logger.info("Skipping this step and downstream TOC steps.")
            return False

        out_path = self.planned_output_path(step, root)
        payload_path = self.planned_payload_path(step, root)

        values = values_for_step(ctx, step)
        rendered_user_prompt, system_prompt, attrs = self.render_prompt_from_library(
            prompt_lib=prompt_lib,
            step=step,
            values=values,
        )

        payload_for_model = rendered_user_prompt
        payload_for_debug = self.build_payload(rendered_user_prompt, inputs)

        runner.set_attributes(**attrs)

        self.print_step_summary(
            step=step,
            input_paths=inputs,
            output_path=out_path,
            payload_chars=len(payload_for_debug),
        )

        self.write_text(payload_path, payload_for_debug)
        logger.info("Wrote debug payload: %s", payload_path)

        if self.wait_before_first_call and self.step_delay_seconds > 0:
            logger.debug("Waiting %ss before API call...", self.step_delay_seconds)
            time.sleep(self.step_delay_seconds)

        logger.debug("Sending to model... (Step %s)", step.code)

        for attempt in range(1, self.max_step_retries + 1):
            start = datetime.now()
            try:
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

                elapsed = datetime.now() - start
                logger.info("Model returned. Elapsed: %s", elapsed)

                self.write_text(out_path, text)
                logger.info("Wrote model output: %s", out_path)
                return True

            except Exception as e:
                msg = str(e)

                status_code = None
                if isinstance(e, requests.exceptions.HTTPError):
                    resp = getattr(e, "response", None)
                    status_code = resp.status_code if resp is not None else None

                if status_code == 402:
                    logger.critical(
                        "FATAL: API spend limit reached (HTTP 402). Error: %s",
                        msg,
                    )
                    raise

                can_retry = status_code in self.retriable_statuses

                if (not can_retry) or (attempt >= self.max_step_retries):
                    logger.error(
                        "Step failed (attempt %s/%s). Status=%s. Error: %s",
                        attempt,
                        self.max_step_retries,
                        status_code,
                        msg,
                    )
                    logger.error(
                        "Giving up on Step %s after %s attempts.",
                        step.code,
                        self.max_step_retries,
                    )
                    return False

                wait_minutes = self.error_delay_seconds / 60
                logger.error(
                    "Step error (attempt %s/%s). Status=%s. Retrying in %g minutes...",
                    attempt,
                    self.max_step_retries,
                    status_code,
                    wait_minutes,
                )
                time.sleep(self.error_delay_seconds)

        return False