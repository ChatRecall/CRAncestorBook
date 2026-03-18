# /phases/enrichment/enrichment_ai.py

import logging
from typing import Any
import time

from CRAncestorBook.config import RUN_CONFIG

logger = logging.getLogger(__name__)

def _render_prompt_from_library(
    *,
    prompt_lib: Any,
    prompt_name: str,
    values: dict[str, Any],
) -> tuple[str, str | None, dict[str, Any]]:
    prompt_t, system_prompt = prompt_lib.get_prompt_with_system_prompt(prompt_name)

    if prompt_t is None:
        raise RuntimeError(f"Prompt not found in library: {prompt_name}")

    raw_text = prompt_t.prompt_text
    filled_text = prompt_t.fill_placeholders(values, prompt_text=raw_text)

    attrs = prompt_t.default_attributes.to_dict()
    return filled_text, system_prompt, attrs

def _call_runner_text(
    *,
    runner: Any,
    user_prompt: str,
    system_prompt: str | None,
) -> str:
    last_exc: Exception | None = None

    for attempt in range(1, RUN_CONFIG.max_step_retries + 1):
        try:
            use_stream_collect = callable(getattr(runner, "prompt_stream_collect", None))

            if use_stream_collect:
                text = runner.prompt_stream_collect(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                )
            else:
                response = runner.prompt(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                )
                text = (response.response if response else "") or ""

            text = text or ""
            if text.strip():
                return text

            raise RuntimeError("Model returned empty expansion output.")

        except Exception as exc:
            last_exc = exc
            logger.error(
                "Episode expansion call failed on attempt %d/%d: %s",
                attempt,
                RUN_CONFIG.max_step_retries,
                exc,
            )
            if attempt < RUN_CONFIG.max_step_retries:
                time.sleep(RUN_CONFIG.error_delay_seconds)

    if last_exc:
        raise last_exc
    raise RuntimeError("Episode expansion call failed with unknown error.")

