# book_context.py

from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ChapterInfo:
    number: int
    title: str
    time_range: str
    examples: list[str]

    @property
    def scope_text(self) -> str:
        return f"Chapter {self.number}: {self.title} ({self.time_range})"

    @property
    def chapter_list_text(self) -> str:
        return f"Chapter {self.number}: {self.title} ({self.time_range}) \nExamples:{self.examples}"

@dataclass(frozen=True)
class BookContext:
    root: Path                      # work_dir
    book_title: str
    primary_sources: list[Path]
    secondary_sources: list[Path]
    official_sources: list[Path]
    chapters: dict[int, ChapterInfo]

    @property
    def all_sources(self) -> list[Path]:
        return [*self.primary_sources, *self.secondary_sources, *self.official_sources]

    @property
    def chapter_list_text(self) -> str:
        """
        Long chapter list intended for << chapter_list >> in prompts.
        Includes title, time range, and illustrative examples.
        """
        blocks: list[str] = []
        for n in sorted(self.chapters):
            c = self.chapters[n]
            lines: list[str] = []
            lines.append(f"**Chapter {n}: {c.title}**")
            lines.append(f"- Time Range: {c.time_range}")
            if c.examples:
                lines.append("- Events during this period include, but are not limited to:")
                lines.extend([f"  - {x}" for x in c.examples])
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def chapter(self, n: int) -> ChapterInfo:
        return self.chapters[n]

def load_book_context(book_cfg: dict[str, Any]) -> BookContext:
    root = Path(book_cfg["paths"]["work_dir"]).expanduser()

    def _paths(items: list[str]) -> list[Path]:
        return [root / p for p in items]

    title = book_cfg["target"]["name"]
    primary = _paths(book_cfg["sources"]["primary"])
    secondary = _paths(book_cfg["sources"]["secondary"])
    official = _paths(book_cfg["sources"]["official"])

    chapters_cfg = book_cfg.get("chapters", {})
    chapters: dict[int, ChapterInfo] = {}
    for k, v in chapters_cfg.items():
        n = int(k)
        examples = v.get("examples") or []
        if not isinstance(examples, list):
            raise ValueError(f"Invalid chapters.{k}.examples: expected list[str]")
        chapters[n] = ChapterInfo(
            number=n,
            title=v["title"],
            time_range=v["time_range"],
            examples=[str(x) for x in examples],
        )

    return BookContext(
        root=root,
        book_title=title,
        primary_sources=primary,
        secondary_sources=secondary,
        official_sources=official,
        chapters=chapters,
    )
