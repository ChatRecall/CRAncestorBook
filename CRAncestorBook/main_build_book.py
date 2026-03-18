# main_build_book.py

from pathlib import Path
import tomllib
import logging

from WrapEmit import configure_cli


from CRAncestorBook.book_build import build_book_markdown, OUTPUT_MD_NAME, OUTPUT_YAML_NAME, DEFAULT_CHAPTER_FILENAME, toml_to_pandoc_metadata
from CRAncestorBook.core import configure_logging, load_book_context, prompt_toml_path

logger = logging.getLogger(__name__)

def main() -> None:
    configure_logging()
    configure_cli()

    book_toml = Path(input("book.toml path: ").strip()).expanduser().resolve()
    if not book_toml.exists():
        raise FileNotFoundError(book_toml)

    # Your layout: <root>/book/book.toml
    book_dir = book_toml.parent
    project_root = book_dir.parent
    chapters_root = project_root / "Chapters"

    cfg = tomllib.loads(book_toml.read_text(encoding="utf-8"))
    ctx = load_book_context(cfg)

    # Optional per-chapter append files (synced into workspace by env_prep)
    paths = cfg.get("paths", {}) or {}
    if not isinstance(paths, dict):
        paths = {}
    appends_dst_rel = Path(str(paths.get("chapter_appends_dst") or "book/chapter_appends"))
    chapter_appends_dir = project_root / appends_dst_rel

    chapter_append_map: dict[int, str] = {}
    chapters_tbl = cfg.get("chapters", {}) or {}
    if isinstance(chapters_tbl, dict):
        for k, ch_cfg in chapters_tbl.items():
            try:
                n = int(k)
            except Exception:
               continue
            if not isinstance(ch_cfg, dict):
                continue
            name = ch_cfg.get("append_md")

            if isinstance(name, str) and name.strip():
                chapter_append_map[n] = name.strip()

    # Front/back matter live next to book.toml
    front_matter = book_dir / "front_matter.md"
    back_matter = book_dir / "back_matter.md"

    output_md = book_dir / OUTPUT_MD_NAME
    output_yaml = book_dir / OUTPUT_YAML_NAME

    # Let you override which chapter artifact to compile
    raw_ch_file = input(f"Chapter filename [{DEFAULT_CHAPTER_FILENAME}]: ").strip()
    chapter_filename = raw_ch_file or DEFAULT_CHAPTER_FILENAME

    toml_to_pandoc_metadata(book_toml, output_yaml)
    build_book_markdown(
        ctx,
        project_root=project_root,
        book_dir=book_dir,
        chapters_root=chapters_root,
        chapter_filename=chapter_filename,
        output_md=output_md,
        front_matter_md=front_matter,
        back_matter_md=back_matter,
        chapter_appends_dir=chapter_appends_dir,
        chapter_append_map=chapter_append_map,
    )

    print(f"Wrote: {output_md}")
    print(f"Wrote: {output_yaml}")


if __name__ == "__main__":
    main()

