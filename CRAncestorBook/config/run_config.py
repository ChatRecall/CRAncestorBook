# config/run_config.py
from dataclasses import dataclass
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class RunConfig:
    step_delay_seconds: int
    chapter_delay_seconds: int
    max_step_retries: int
    error_delay_seconds: int
    retriable_statuses: FrozenSet[int]
    wait_before_first_call: bool
    use_streaming:bool


RUN_CONFIG = RunConfig(
    step_delay_seconds=10,
    chapter_delay_seconds=10,
    max_step_retries=8,
    error_delay_seconds=180,
    retriable_statuses=frozenset({429, 500, 502, 503, 504}),
    wait_before_first_call=False,
    use_streaming=True,
)
