# step_validation.py

from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Iterable

@dataclass(frozen=True)
class GlobRequirement:
    pattern: str
    missing_msg: str


@dataclass(frozen=True)
class StepPrereqs:
    required_dirs: tuple[str, ...] = ()
    required_globs: tuple[GlobRequirement, ...] = ()

def ensure_required_dirs(book_root: Path, required: Iterable[str]) -> tuple[bool, str]:
    missing = [book_root / rel for rel in required if not (book_root / rel).exists()]
    if missing:
        return False, "Missing required folders:\n" + "\n".join(f" - {p}" for p in missing)
    return True, ""


def verify_step_prereqs(book_root: Path, prereqs: StepPrereqs) -> tuple[bool, str]:
    ok, msg = ensure_required_dirs(book_root, prereqs.required_dirs)
    if not ok:
        return ok, msg

    for req in prereqs.required_globs:
        matches = list(book_root.glob(req.pattern))
        if not matches:
            return False, req.missing_msg

    return True, ""