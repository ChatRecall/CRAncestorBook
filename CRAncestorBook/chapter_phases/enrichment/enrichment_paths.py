# phases/enrichment/enrichment_paths.py

from pathlib import Path
import logging

from CRAncestorBook.core import (
    BookContext,
    CODE_STYLE_POLISH,
    CODE_ENRICHMENT_FINAL,
    EPISODE_INDEX_STEM,
    EPISODE_ELIGIBILITY_STEM,
    EPISODE_RETRIEVAL_STEM,
    EPISODE_RETRIEVAL_REVIEW_STEM,
    EPISODE_EXPANSIONS_STEM,
    EPISODE_EVALUATIONS_STEM,
    EPISODE_DECISIONS_STEM,
    EPISODE_REASSEMBLED_STEM
)
from CRAncestorBook.paths import chapter_path

logger = logging.getLogger(__name__)

def _phase_style_final_input_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, CODE_STYLE_POLISH)

def _episode_index_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_INDEX_STEM, ext=".json")

def _episode_eligibility_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_ELIGIBILITY_STEM, ext=".json")

def _episode_retrieval_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_RETRIEVAL_STEM, ext=".json")

def _episode_retrieval_review_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_RETRIEVAL_REVIEW_STEM, ext=".json")

def _episode_expansions_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_EXPANSIONS_STEM, ext=".json")

def _episode_evaluations_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_EVALUATIONS_STEM, ext=".json")

def _episode_decisions_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_DECISIONS_STEM, ext=".json")

def _episode_reassembled_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, EPISODE_REASSEMBLED_STEM)

def _enrichment_final_path(ctx: BookContext, chapter_n: int) -> Path:
    return chapter_path(ctx.root, chapter_n, CODE_ENRICHMENT_FINAL)


