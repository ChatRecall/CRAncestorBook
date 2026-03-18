# pipeline_plan.py

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class StepNumberPlan:
    """
    Human-facing numeric step labels mapped to stable phase keys.
    This is the ONLY place you renumber/reorder numeric steps.
    """
    number_to_phase: dict[int, str]

    def allowed_steps(self) -> set[int]:
        return set(self.number_to_phase.keys())

    def phase_ids_for(self, steps: Sequence[int]) -> list[str]:
        return [self.number_to_phase[n] for n in steps]


# ---- CURRENT MAPPING (ONE PLACE) ----

DEFAULT_STEP_PLAN = StepNumberPlan(
    number_to_phase={
        1: "toc",
        2: "draft",
        3: "coverage",
        4: "dedup",
        5: "style",
        6: "enrichment",
        7: "paragraph",
    }
)

