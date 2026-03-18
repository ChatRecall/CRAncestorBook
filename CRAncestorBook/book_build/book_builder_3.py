# book_builder_3.py

from datetime import date
from pathlib import Path
from typing import Optional
import re
import tomllib


# -----------------------------
# Config you may tweak
# -----------------------------

DEFAULT_CHAPTER_FILENAME = "paragraph_polish.md"
OUTPUT_MD_NAME = "book.md"
OUTPUT_YAML_NAME = "metadata.yaml"
SEPARATOR = "\n\n- - -\n\n"


# -----------------------------
# Minimal BookContext adapter
# -----------------------------
# This expects your existing book_context.py to provide:
#   - load_book_context(cfg: dict) -> BookContext
#   - ctx.root (Path)
#   - ctx.chapters (dict[int, ...])
#   - ctx.chapter(n) with fields: number, title, time_range
#
# If your BookContext API differs, adjust here.
from CRAncestorBook.core import load_book_context, BookContext


_CHAPTER_HEADING_RE = re.compile(
    r"\A\s*(#{1,6})\s*chapter\s*\d+\s*[:\-]?\s*.*?\n",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_optional_md(path: Optional[Path]) -> str:
    if path is None:
        return ""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    text = read_text(path)
    return text if text.endswith("\n") else (text + "\n")


def strip_existing_leading_chapter_header(text: str) -> str:
    """
    If the file begins with a markdown heading like '# Chapter N: ...', remove it.
    Also remove a single italic time-range line immediately after if present.
    """
    m = _CHAPTER_HEADING_RE.match(text)
    if not m:
        return text.lstrip("\ufeff")  # strip BOM if present

    rest = text[m.end():].lstrip()

    # Optional italic time range line: *1908–1912*
    if rest.startswith("*"):
        first_line, _, tail = rest.partition("\n")
        if first_line.endswith("*"):
            return tail.lstrip()

    return rest


def chapter_header_md(*, number: int, title: str, time_range: str) -> str:
    title = (title or "").strip()
    time_range = (time_range or "").strip()

    lines = [f"# Chapter {number}: {title}"]
    if time_range:
        lines.append(f"*{time_range}*")
    lines.append("")  # blank line after header block

    return "\n".join(lines) + "\n"


def toml_to_pandoc_metadata(book_toml: Path, out_yaml: Path) -> Path:
    """
    Minimal TOML -> Pandoc metadata YAML.
    Keeps this boring and stable: title, subtitle, author, lang, publisher, rights, date.
    """
    cfg = tomllib.loads(book_toml.read_text(encoding="utf-8"))
    book = cfg.get("book", {})
    if not isinstance(book, dict):
        raise ValueError("Missing or invalid [book] table in book.toml")

    # Map your TOML keys -> pandoc keys
    mapping = {
        "title": "title",
        "subtitle": "subtitle",
        "author": "author",
        "language": "lang",
        "publisher": "publisher",
        "rights": "rights",
        "date": "date",
        "year": "date",
    }

    meta: dict[str, str] = {}
    for src, dst in mapping.items():
        v = book.get(src)
        if v is None or v == "":
            continue
        meta[dst] = str(v)

    # Ensure date exists
    if "date" not in meta:
        meta["date"] = date.today().isoformat()

    def yaml_quote(s: str) -> str:
        # Simple, safe quoting for one-line scalars
        s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{s}"'

    lines = [f"{k}: {yaml_quote(v)}" for k, v in meta.items()]
    out_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_yaml


def build_book_markdown(
    ctx: BookContext,
    *,
    project_root: Path,
    book_dir: Path,
    chapters_root: Path,
    chapter_filename: str,
    output_md: Path,
    front_matter_md: Optional[Path],
    back_matter_md: Optional[Path],
    chapter_appends_dir: Optional[Path] = None,
    chapter_append_map: Optional[dict[int, str]] = None,
    separator: str = SEPARATOR,
) -> Path:
    """
    Writes: front + chapters + back into output_md.
    Chapters are read from: chapters_root / f"Chapter_{N}" / chapter_filename
    """
    front = read_optional_md(front_matter_md)
    back = read_optional_md(back_matter_md)

    chapter_nums = sorted(ctx.chapters.keys())
    output_md.parent.mkdir(parents=True, exist_ok=True)

    with output_md.open("w", encoding="utf-8") as out:
        if front.strip():
            out.write(front.rstrip() + "\n")
            out.write(separator)

        for i, n in enumerate(chapter_nums):
            ch = ctx.chapter(n)
            chapter_dir = chapters_root / f"Chapter_{n}"
            path = chapter_dir / chapter_filename
            if not path.exists():
                raise FileNotFoundError(f"Missing chapter file: {path}")

            raw = read_text(path)
            body = strip_existing_leading_chapter_header(raw).lstrip()

            header = chapter_header_md(
                number=getattr(ch, "number", n),
                title=getattr(ch, "title", f"Chapter {n}"),
                time_range=getattr(ch, "time_range", ""),
            )

            if i > 0:
                out.write(separator)

            out.write(header)
            out.write("\n")
            out.write(body.rstrip() + "\n")

            # Optional per-chapter append (e.g., image links)
            append_name = (chapter_append_map or {}).get(n)
            if append_name:
                if chapter_appends_dir is None:
                    raise ValueError(
                        f"append_md set for chapter {n} but chapter_appends_dir is None"
                    )

                append_path = chapter_appends_dir / append_name
                if not append_path.exists():
                    raise FileNotFoundError(f"Missing chapter append file: {append_path}")

                append_text = read_text(append_path)
                if not append_text.endswith("\n"):
                    append_text += "\n"

                out.write("\n")
                out.write(append_text.lstrip())


        if back.strip():
            out.write(separator)
            out.write(back.lstrip())

    return output_md


