# core/__init__.py

from .book_context import BookContext, load_book_context
from .constants import (PROVIDER_API_KEYS,
                        BOOK_LOCATION,
                        CODE_INITIAL_DRAFT,
                        CODE_COMP_AUDIT,
                        CODE_COMP_DRAFT,
                        CODE_DUP_DETECT,
                        CODE_DUP_COMBINE,
                        CODE_DUP_RESOLVE,
                        CODE_STYLE_POLISH,

                        CODE_EPISODE_DECOMPOSE,
                        CODE_EPISODE_EXPAND,
                        CODE_EPISODE_EVALUATE,
                        CODE_ENRICHMENT_FINAL,

                        EPISODE_INDEX_STEM,
                        EPISODE_ELIGIBILITY_STEM,
                        EPISODE_RETRIEVAL_STEM,
                        EPISODE_RETRIEVAL_REVIEW_STEM,
                        EPISODE_EXPANSIONS_STEM,
                        EPISODE_EVALUATIONS_STEM,
                        EPISODE_DECISIONS_STEM,
                        EPISODE_REASSEMBLED_STEM,

                        CODE_PARAGRAPH_POLISH,

                        DEFAULT_MODEL,
                        DEFAULT_PROMPT_JSON,
                        DEFAULT_PROVIDER,
                        DEFAULT_EMBED_PROVIDER,
                        )

from .helpers import configure_logging, prompt_toml_path
