# paths/env_prep.py

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import shutil
import tomllib
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnvLayout:
    root: Path
    book_dir: Path
    sources_dir: Path
    planning_dir: Path
    book_toml: Path


@dataclass(frozen=True)
class ChapterEnvLayout(EnvLayout):
    chapters_dir: Path
    ledger_dir: Path


def _has_any_file_under(dirpath: Path) -> bool:
    if not dirpath.is_dir():
        return False
    for p in dirpath.rglob("*"):
        if p.is_file():
            return True
    return False


def prepare_workspace_env(root: Path) -> EnvLayout:
    """
    Minimal workspace guardrails for pre-TOC work:
    - Require book/book.toml
    - Require at least one source document anywhere under Sources/
    - Create Planning/
    - Create book/images as convenience
    """
    root = root.expanduser().resolve()

    book_dir = root / "book"
    sources_dir = root / "Sources"
    planning_dir = root / "Planning"

    book_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)

    book_toml = book_dir / "book.toml"
    if not book_toml.is_file():
        raise FileNotFoundError(f"Missing required book config: {book_toml}")

    if not _has_any_file_under(sources_dir):
        raise FileNotFoundError(
            f"No source documents found under: {sources_dir} "
            f"(need at least one file somewhere in Sources/...)"
        )

    (book_dir / "images").mkdir(parents=True, exist_ok=True)
    planning_dir.mkdir(parents=True, exist_ok=True)
    (planning_dir / "payloads").mkdir(parents=True, exist_ok=True)

    return EnvLayout(
        root=root,
        book_dir=book_dir,
        sources_dir=sources_dir,
        planning_dir=planning_dir,
        book_toml=book_toml,
    )


def prepare_chapter_env(root: Path, *, chapter_nums: Iterable[int]) -> ChapterEnvLayout:
    """
    Chapter-stage guardrails:
    - Require workspace env first
    - Create Chapters/
    - Create Ledger/
    - Create Chapter_N folders
    """
    base = prepare_workspace_env(root)

    chapters_dir = root / "Chapters"
    ledger_dir = root / "Ledger"

    chapters_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "payloads").mkdir(parents=True, exist_ok=True)

    for n in chapter_nums:
        (chapters_dir / f"Chapter_{n}").mkdir(parents=True, exist_ok=True)

    return ChapterEnvLayout(
        root=base.root,
        book_dir=base.book_dir,
        sources_dir=base.sources_dir,
        planning_dir=base.planning_dir,
        book_toml=base.book_toml,
        chapters_dir=chapters_dir,
        ledger_dir=ledger_dir,
    )


def _copy_replace(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"Missing source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_dir_replace(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Missing source directory: {src_dir}")
    dst_dir.mkdir(parents=True, exist_ok=True)

    for p in src_dir.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src_dir)
            _copy_replace(p, dst_dir / rel)


def _src_root_for_group(cfg_paths: dict, group: str) -> Path:
    key = f"{group}_sources"
    val = cfg_paths.get(key, "")
    if not val:
        raise ValueError(f"Missing [paths].{key} in book.toml")
    return Path(val).expanduser().resolve()


def sync_workspace_from_toml(book_toml_path: Path) -> Path:
    """
    Materialize workspace:
    - work_dir is the destination root
    - copy this TOML into work_dir/book/book.toml (replace)
    - copy all listed source files into work_dir/<their listed path> (replace)
    - copy images, appends, and book materials into workspace
    """
    book_toml_path = book_toml_path.expanduser().resolve()
    cfg = tomllib.loads(book_toml_path.read_text(encoding="utf-8"))

    cfg_paths = cfg.get("paths", {})
    if not isinstance(cfg_paths, dict):
        raise ValueError("Missing or invalid [paths] table in book.toml")

    work_dir_val = cfg_paths.get("work_dir", "")
    if not work_dir_val:
        raise ValueError("Missing [paths].work_dir in book.toml")

    work_dir = Path(work_dir_val).expanduser().resolve()
    (work_dir / "book").mkdir(parents=True, exist_ok=True)

    _copy_replace(book_toml_path, work_dir / "book" / "book.toml")

    cfg_sources = cfg.get("sources", {})
    if not isinstance(cfg_sources, dict):
        raise ValueError("Missing or invalid [sources] table in book.toml")

    primary_root = _src_root_for_group(cfg_paths, "primary")
    secondary_root = _src_root_for_group(cfg_paths, "secondary")
    official_root = _src_root_for_group(cfg_paths, "official")

    group_roots = {
        "primary": primary_root,
        "secondary": secondary_root,
        "official": official_root,
    }

    for group in ("primary", "secondary", "official"):
        rel_list = cfg_sources.get(group, [])
        if rel_list is None:
            rel_list = []
        if not isinstance(rel_list, list):
            raise ValueError(f"[sources].{group} must be a list")

        src_root = group_roots[group]

        for rel_str in rel_list:
            rel_dst = Path(rel_str)
            parts = rel_dst.parts
            if len(parts) < 3 or parts[0] != "Sources" or parts[1] != group:
                raise ValueError(
                    f"Expected path like 'Sources/{group}/...'; got: {rel_str}"
                )

            rel_within_group = Path(*parts[2:])
            src = src_root / rel_within_group
            dst = work_dir / rel_dst
            _copy_replace(src, dst)

    chapters_tbl = cfg.get("chapters", {})
    if chapters_tbl is None:
        chapters_tbl = {}
    if not isinstance(chapters_tbl, dict):
        raise ValueError("Missing or invalid [chapters] table in book.toml")

    appends_root_val = cfg_paths.get("chapter_appends", "")
    if appends_root_val:
        appends_root = Path(appends_root_val).expanduser().resolve()
        appends_dst_rel = Path(cfg_paths.get("chapter_appends_dst", "book/chapter_appends"))
        appends_dst_dir = work_dir / appends_dst_rel
        appends_dst_dir.mkdir(parents=True, exist_ok=True)

        for _, ch_cfg in chapters_tbl.items():
            if not isinstance(ch_cfg, dict):
                continue
            append_name = ch_cfg.get("append_md", "")
            if isinstance(append_name, str) and append_name.strip():
                _copy_replace(appends_root / append_name, appends_dst_dir / append_name)

    book_materials = cfg.get("book_materials", {})
    if isinstance(book_materials, dict):
        for key in ("cover", "front_matter", "back_matter"):
            val = book_materials.get(key, "")
            if isinstance(val, str) and val.strip():
                src = Path(val).expanduser().resolve()
                dst = work_dir / "book" / src.name
                _copy_replace(src, dst)

    images_root_val = cfg_paths.get("images", "")
    if images_root_val:
        images_root = Path(images_root_val).expanduser().resolve()
        images_dst_rel = Path(cfg_paths.get("images_dst", "book/images"))
        _copy_dir_replace(images_root, work_dir / images_dst_rel)

    return work_dir

