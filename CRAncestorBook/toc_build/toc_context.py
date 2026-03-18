# toc_build/toc_context.py

from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class TOCContext:
    book_toml_path: Path
    project_root: Path
    book_dir: Path
    sources_dir: Path
    planning_dir: Path
    primary_sources_dir: Path | None
    secondary_sources_dir: Path | None
    official_sources_dir: Path | None

    @classmethod
    def from_book_toml(cls, book_toml_path: str | Path) -> "TOCContext":
        book_toml_path = Path(book_toml_path).expanduser().resolve()
        book_dir = book_toml_path.parent
        project_root = book_dir.parent
        sources_dir = project_root / "Sources"
        planning_dir = project_root / "Planning"

        primary_sources_dir = sources_dir / "primary"
        secondary_sources_dir = sources_dir / "secondary"
        official_sources_dir = sources_dir / "official"

        return cls(
            book_toml_path=book_toml_path,
            project_root=project_root,
            book_dir=book_dir,
            sources_dir=sources_dir,
            planning_dir=planning_dir,
            primary_sources_dir=primary_sources_dir,
            secondary_sources_dir=secondary_sources_dir,
            official_sources_dir=official_sources_dir,
        )

    @property
    def root(self) -> Path:
        """Alias to match existing pipeline style."""
        return self.project_root

    @property
    def all_source_dirs(self) -> list[Path]:
        return [
            p
            for p in (
                self.primary_sources_dir,
                self.secondary_sources_dir,
                self.official_sources_dir,
            )
            if p is not None
        ]

    @property
    def existing_source_dirs(self) -> list[Path]:
        return [p for p in self.all_source_dirs if p.exists() and p.is_dir()]

    @property
    def has_any_sources(self) -> bool:
        return bool(self.existing_source_dirs)

    @property
    def payloads_dir(self) -> Path:
        return self.planning_dir / "payloads"

    @property
    def event_inventory_path(self) -> Path:
        return self.planning_dir / "toc_event_inventory.txt"

    @property
    def stage_grouped_events_path(self) -> Path:
        return self.planning_dir / "toc_stage_grouped_events.txt"

    @property
    def chapter_breakpoints_path(self) -> Path:
        return self.planning_dir / "toc_chapter_breakpoints.txt"

    @property
    def draft_chapters_path(self) -> Path:
        return self.planning_dir / "toc_draft_chapters.txt"

    @property
    def approved_chapters_path(self) -> Path:
        return self.planning_dir / "toc_approved_chapters.txt"

    @property
    def chapter_examples_path(self) -> Path:
        return self.planning_dir / "toc_chapter_examples.txt"

    @property
    def generated_toml_path(self) -> Path:
        return self.planning_dir / "chapters.generated.toml"

    @property
    def approved_chapters_exists(self) -> bool:
        return self.approved_chapters_path.exists()

    @property
    def generated_toml_exists(self) -> bool:
        return self.generated_toml_path.exists()

    def ensure_planning_dirs(self) -> None:
        self.planning_dir.mkdir(parents=True, exist_ok=True)
        self.payloads_dir.mkdir(parents=True, exist_ok=True)

    def missing_source_dirs(self) -> list[Path]:
        return [p for p in self.all_source_dirs if not p.exists()]

    def all_source_files(self) -> list[Path]:
        files: list[Path] = []
        for source_dir in self.existing_source_dirs:
            files.extend(sorted(p for p in source_dir.iterdir() if p.is_file()))
        return files
