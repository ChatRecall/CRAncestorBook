# pipeline_registry.py

from dataclasses import dataclass
from typing import Callable, TypeAlias

from .pipeline_plan import StepNumberPlan, DEFAULT_STEP_PLAN

# Import runners
from CRAncestorBook.chapter_phases import run_phase_draft
from CRAncestorBook.chapter_phases import run_phase_coverage
from CRAncestorBook.chapter_phases import run_phase_dedup
from CRAncestorBook.chapter_phases import run_phase_style

from CRAncestorBook.chapter_phases import run_phase_enrichment

from CRAncestorBook.chapter_phases import run_phase_paragraph

PhaseRunner: TypeAlias = Callable[..., None]


@dataclass(frozen=True, slots=True)
class Phase:
    """
    A top-level runnable pipeline phase.
    """
    key: str          # stable id: "draft", "coverage", ...
    label: str        # UI/log label
    run: PhaseRunner  # run_stepN function


@dataclass(frozen=True, slots=True)
class PipelineRegistry:
    """
    Registry mapping numeric steps -> phases -> runner functions.
    """
    plan: StepNumberPlan
    phases: dict[str, Phase]

    def allowed_steps(self) -> set[int]:
        return self.plan.allowed_steps()

    def phase_for_step(self, step_n: int) -> Phase:
        phase_key = self.plan.number_to_phase[step_n]
        return self.phases[phase_key]


# ---- CURRENT REGISTRY DATA (ONE PLACE) ----
### --- GET RID OF phases.key FIELD AND JUST USE DICT KEY
DEFAULT_PIPELINE_REGISTRY = PipelineRegistry(
    plan=DEFAULT_STEP_PLAN,
    phases={
        "draft": Phase(
            key="draft",
            label="Initial Chapter Draft",
            run=run_phase_draft,
        ),
        "coverage": Phase(
            key="coverage",
            label="Coverage (Audit + Inclusion)",
            run=run_phase_coverage,
        ),
        "dedup": Phase(
            key="dedup",
            label="Dedup (Detect + Combine + Resolve)",
            run=run_phase_dedup,
        ),
        "style": Phase(
            key="style",
            label="Style Polish",
            run=run_phase_style,
        ),

        "enrichment": Phase(
            key="enrichment",
            label="Enrichment",
            run=run_phase_enrichment,
        ),

        "paragraph": Phase(
            key="paragraph",
            label="Paragraph Polish",
            run=run_phase_paragraph,
        ),
    },
)

