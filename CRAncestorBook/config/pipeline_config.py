# config/pipeline_config.py

DEFAULT_MODEL = "openai-gpt-54"

MODELS_SUBSTEP = {

    # Step 1 TOC  (structured reasoning)
    "toc_extract_events": "qwen3-235b-a22b-thinking-2507",
    "toc_map_stages": "qwen3-235b-a22b-thinking-2507",
    "toc_detect_breakpoints": "qwen3-235b-a22b-thinking-2507",
    "toc_generate_chapters": "openai-gpt-54",
    "toc_generate_examples": "openai-gpt-54",
    "toc_generate_toml": "openai-gpt-54",

    # Step 2  (long narrative drafting)
    "initial_draft": "openai-gpt-54", # updated temporarily to test

    # Step 3 substeps (analysis + writing)
    "comp_audit": "qwen3-235b-a22b-thinking-2507",
    "comp_draft": "openai-gpt-54",

    # Step 4 substeps (dedup reasoning)
    "dup_detect": "qwen3-235b-a22b-thinking-2507",
    "dup_combine": "qwen3-235b-a22b-thinking-2507",
    "dup_resolve": "openai-gpt-54",

    # Step 5 (style)
    "style_polish": "openai-gpt-54",

    # Step 6 enrichment
    "episode_decompose": "openai-gpt-54",     # schema heavy
    "episode_expand": "openai-gpt-54",    # prose expansion
    "episode_evaluate": "openai-gpt-54",      # strict evaluator
    "enrichment_final": "openai-gpt-54",  # narrative recombine

    # Step 7 (chapter flow)
    "paragraph_polish": "openai-gpt-54",

}

'''
# Superseded
# Step 2
    "initial_draft": "openai-gpt-54",

    # Step 3 substeps
    "comp_audit": "qwen3-235b-a22b-thinking-2507",
    "comp_draft": "openai-gpt-54",

    # Step 4 substeps
    "dup_detect": "qwen3-235b-a22b-thinking-2507",
    "dup_combine": "qwen3-235b-a22b-thinking-2507",
    "dup_resolve": "openai-gpt-54",

    # Step 5
    "style_polish": "qwen3-235b-a22b-instruct-2507",
 
 # Step 6
    "episode_decompose": "openai-gpt-54",    # Step 7
    "paragraph_polish": "qwen3-235b-a22b-instruct-2507",   
    
'''

def get_model_substep(key: str) -> str:
    return MODELS_SUBSTEP.get(key, DEFAULT_MODEL)
