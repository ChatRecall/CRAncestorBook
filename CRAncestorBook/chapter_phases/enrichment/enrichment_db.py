# phases/enrichment/enrichment_db.py

import re
from pathlib import Path
import logging

from CRAncestorBook.core import BookContext, DEFAULT_EMBED_PROVIDER

from WrapEmit import info
from WrapEmbed.ingest import ingest_texts
from WrapEmbed.query import open_embedder
from WrapEmbed.schema_inspect import open_store, summarize_sources
from WrapEmbed.utils.db_layout import resolve_db_layout

logger = logging.getLogger(__name__)

def _build_embed_project_slug(ctx: BookContext) -> str:
    """
    Derive a stable embed project slug from the book title.

    Example:
        "Harvey Irwin" -> "Harvey_Irwin"
    """
    title = (ctx.book_title or "").strip()

    if not title:
        return "book_project"

    slug = re.sub(r"\W+", "_", title)
    return slug.strip("_")

def _rel_files(root: Path, paths: list[Path]) -> list[str]:
    return [str(p.relative_to(root)) for p in paths]

def _open_or_build_enrichment_db(ctx: BookContext):
    project = _build_embed_project_slug(ctx)
    data_dir = ctx.root
    provider = DEFAULT_EMBED_PROVIDER
    persist_root = ctx.root / "_vectordb"

    primary_files = _rel_files(ctx.root, ctx.primary_sources)
    secondary_files = _rel_files(ctx.root, ctx.secondary_sources)
    official_files = _rel_files(ctx.root, ctx.official_sources)

    if not primary_files and not secondary_files and not official_files:
        raise RuntimeError("No source files available for enrichment vector DB.")

    layout = resolve_db_layout(
        data_dir=data_dir,
        project=project,
        collection=None,
        persist_root=persist_root,
    )

    needs_ingest = True

    if layout.persist_dir.exists() and any(layout.persist_dir.iterdir()):
        try:
            opened = open_store(
                data_dir=data_dir,
                project=project,
                collection=None,
                persist_root=persist_root,
                distance_space="cosine",
            )
            existing_chunks = opened.store.count()
            needs_ingest = existing_chunks == 0
            info(
                f"Existing enrichment DB check: project={project} "
                f"persist_dir={layout.persist_dir} chunks={existing_chunks}"
            )
        except Exception:
            needs_ingest = True

    if needs_ingest:
        result = None
        info(
            f"Building enrichment vector DB: project={project} "
            f"provider={provider} sources={len(primary_files) + len(secondary_files) + len(official_files)}"
        )
        if primary_files:
            result = ingest_texts(
                data_dir=data_dir,
                project=project,
                provider=provider,
                persist_root=persist_root,
                files=primary_files,
                source_type="primary",
            )
            info(result.summary())

        if secondary_files:
            result = ingest_texts(
                data_dir=data_dir,
                project=project,
                provider=provider,
                persist_root=persist_root,
                files=secondary_files,
                source_type="secondary",
            )
            info(result.summary())

        if official_files:
            result = ingest_texts(
                data_dir=data_dir,
                project=project,
                provider=provider,
                persist_root=persist_root,
                files=official_files,
                source_type="official",
            )
            info(result.summary())
    else:
        info(
            f"Using existing enrichment vector DB: project={project} "
            f"provider={provider} persist_dir={layout.persist_dir} "
            f"sources={len(primary_files) + len(secondary_files) + len(official_files)}"
        )

    open_result = open_embedder(
        data_dir=data_dir,
        project=project,
        persist_root=ctx.root / "_vectordb",
        provider=provider,
    )
    return open_result.embedder

def _log_enrichment_db_summary(ctx: BookContext) -> None:
    project = _build_embed_project_slug(ctx)
    persist_root = ctx.root / "_vectordb"

    opened = open_store(
        data_dir=ctx.root,
        project=project,
        collection=None,
        persist_root=persist_root,
        distance_space="cosine",
    )

    store = opened.store
    res = summarize_sources(
        store=store,
        where={"project": project},
        preview_first=1,
        preview_last=1,
        page_size=500,
    )

    info(f"Enrichment DB summary: project={project}")
    info(f"Persist dir: {opened.persist_dir}")
    info(f"Collection: {opened.collection}")
    info(f"Sources found: {len(res.summaries)}")
    info(f"Total chunks: {store.count()}")

    rows = list(res.summaries.values())
    rows.sort(key=lambda r: (-r.n_chunks, r.source_id))

    for row in rows:
        info(
            f"DB source: id={row.source_id} "
            f"type={row.source_type or '-'} "
            f"chunks={row.n_chunks} "
            f"title={row.source_title or '-'} "
            f"embed={(row.embed_provider or '-')}/{(row.embed_model or '-')}"
        )

