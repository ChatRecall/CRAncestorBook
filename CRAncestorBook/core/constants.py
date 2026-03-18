# constants

from pathlib import Path

from WrapAI.core.wv_core import PROVIDER_OPENAI as PROVIDER_OPENAI_AI, PROVIDER_VENICE as PROVIDER_VENICE_AI
from WrapEmbed.providers import PROVIDER_VENICE as PROVIDER_VENICE_EMBED


# Provider
DEFAULT_PROVIDER = PROVIDER_VENICE_AI  # or PROVIDER_OPENAI
DEFAULT_EMBED_PROVIDER = PROVIDER_VENICE_EMBED
DEFAULT_EMBED_MODEL = "text-embedding-bge-m3"


PROVIDER_API_KEYS = {
    PROVIDER_VENICE_AI: "VENICE_API_KEY",
    PROVIDER_OPENAI_AI: "OPENAI_API_KEY",
}

## used by main
DEFAULT_BOOK_TOML = Path("/home/dave/Data/Current/Projects/Ancestor/Book_3/book.toml")
# ALLOWED_STEPS = {2, 3, 4, 5, 6}

## used by book_pipeline_ai
DEFAULT_MODEL = "zai-org-glm-4.7"
DEFAULT_PROMPT_JSON = Path("/home/dave/Data/Current/Projects/Ancestor/Book_3/Prompts/ancestor_prompts_3.json")

## used by book_builder_toml_to_yaml
BOOK_LOCATION = Path("/home/dave/Data/Current/Projects/Ancestor/Book/Grandpa52/book")

# ------------------------------------------------------
CODE_INITIAL_DRAFT = "initial_draft" # STEP2

CODE_COMP_AUDIT = "comp_audit" # STEP3A
CODE_COMP_DRAFT = "comp_draft" # STEP3B

CODE_DUP_DETECT = "dup_detect" # STEP4A
CODE_DUP_COMBINE = "dup_combine" # STEP4B
CODE_DUP_RESOLVE = "dup_resolve" # STEP4C

CODE_STYLE_POLISH = "style_polish" # STEP5

CODE_EPISODE_DECOMPOSE = "episode_decompose"      # STEP6A
CODE_EPISODE_EXPAND = "episode_expand"            # STEP6B
CODE_EPISODE_EVALUATE = "episode_evaluate"        # STEP6C
CODE_ENRICHMENT_FINAL = "enrichment_final"        # STEP6 FINAL

EPISODE_INDEX_STEM = "episode_index"
EPISODE_ELIGIBILITY_STEM = "episode_eligibility"
EPISODE_RETRIEVAL_STEM = "episode_retrieval"
EPISODE_RETRIEVAL_REVIEW_STEM = "episode_retrieval_review"
EPISODE_EXPANSIONS_STEM = "episode_expansions"
EPISODE_EVALUATIONS_STEM = "episode_evaluations"
EPISODE_DECISIONS_STEM = "episode_decisions"
EPISODE_REASSEMBLED_STEM = "episode_reassembled"

CODE_PARAGRAPH_POLISH = "paragraph_polish" # STEP7

# ------------------------------------------------------

CHAPTER_OUTPUT_TEMPLATE = "Chapters/Chapter_{N}/{filename}"
CHAPTER_PAYLOAD_TEMPLATE = "Ledger/payloads/Chapter_{N}_{code}_payload.txt"
GLOBAL_PAYLOAD_TEMPLATE = "Ledger/payloads/{code}_payload.txt"