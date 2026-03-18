# pipeline/definitions.py
from dataclasses import dataclass


@dataclass(frozen=True)
class StepDefinition:
    code: str
    name: str
    prompt_name: str

    # Keep these as *patterns* so Step modules control paths exactly.
    output_relpath_pattern: str
    payload_relpath_pattern: str
