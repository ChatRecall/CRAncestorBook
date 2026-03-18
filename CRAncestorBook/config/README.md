# Model Selection Strategy for CRAncestorBook Pipeline

## Overview

Different steps in the pipeline require different model strengths. Using the same model for every stage (e.g., GPT-5.4) is suboptimal because the tasks vary widely: reasoning, structured analysis, narrative writing, evaluation, and editorial polishing.

The pipeline performs best when models are assigned according to their strengths.

---

# Model Skill Categories

### 1. Reasoning / Analytical Tasks

Used for classification, comparison, deduplication, and structural decisions.

Best models:

* **Qwen 3 235B Thinking**
* **Kimi K2 Thinking**
* **Claude Opus**
* **GPT-5.4**

Recommended default:

```
qwen3-235b-a22b-thinking-2507
```

---

### 2. Narrative Generation

Used for drafting biography text and expanding episodes.

Best models:

* **Claude Sonnet 4.6**
* **Claude Opus 4.6**
* **GPT-5.4**
* **Gemini 3.1 Pro**

Recommended default:

```
claude-sonnet-4-6
```

Claude models currently produce the most natural long-form narrative style.

---

### 3. Strict JSON / Evaluation Tasks

Used for schema output, validation, and rule-based evaluation.

Best models:

* **GPT-5.4**
* **DeepSeek v3**
* **Kimi Thinking**
* **Qwen Thinking**

Recommended default:

```
openai-gpt-54
```

GPT-5.4 is the most reliable for structured output and strict prompt adherence.

---

### 4. Editing / Polishing

Used for rewriting text smoothly while preserving meaning.

Best models:

* **Claude Sonnet 4.6**
* **Claude Opus 4.6**
* **GPT-5.4**

Recommended default:

```
claude-sonnet-4-6
```

For final chapter polish, Opus often produces the best narrative flow.

---

# Recommended Model Assignment

```
MODELS_SUBSTEP = {

    # Step 1 TOC (reasoning / structure)
    "toc_extract_events": "qwen3-235b-a22b-thinking-2507",
    "toc_map_stages": "qwen3-235b-a22b-thinking-2507",
    "toc_detect_breakpoints": "qwen3-235b-a22b-thinking-2507",
    "toc_generate_chapters": "openai-gpt-54",
    "toc_generate_examples": "openai-gpt-54",
    "toc_generate_toml": "openai-gpt-54",

    # Step 2 Initial Draft (narrative generation)
    "initial_draft": "claude-sonnet-4-6",

    # Step 3 Composition
    "comp_audit": "qwen3-235b-a22b-thinking-2507",
    "comp_draft": "claude-sonnet-4-6",

    # Step 4 Deduplication
    "dup_detect": "qwen3-235b-a22b-thinking-2507",
    "dup_combine": "qwen3-235b-a22b-thinking-2507",
    "dup_resolve": "claude-sonnet-4-6",

    # Step 5 Style polish
    "style_polish": "claude-sonnet-4-6",

    # Step 6 Episode enrichment
    "episode_decompose": "openai-gpt-54",
    "episode_expand": "claude-sonnet-4-6",
    "episode_evaluate": "openai-gpt-54",
    "enrichment_final": "claude-sonnet-4-6",

    # Step 7 Final chapter polish
    "paragraph_polish": "claude-opus-4-6",

}
```

---

# Model Roles in the Pipeline

### Qwen Thinking

Best for:

* classification
* structural reasoning
* deduplication
* chapter structure analysis

---

### Claude Sonnet

Best for:

* narrative drafting
* rewriting paragraphs
* episode expansion
* stylistic improvements

Produces very natural biography prose.

---

### Claude Opus

Best for:

* final editorial polishing
* narrative flow across entire chapters

Particularly strong at smoothing paragraph transitions.

---

### GPT-5.4

Best for:

* strict rule-following
* JSON schema generation
* evaluators and validators
* complex prompt logic

---

# Models Less Suitable for This Pipeline

Avoid for core steps:

| Model    | Reason                            |
| -------- | --------------------------------- |
| DeepSeek | stronger at coding than narrative |
| Mistral  | smaller model                     |
| Gemma    | weaker reasoning                  |
| Hermes   | creative but less structured      |
| Grok     | inconsistent style                |

---

# Ideal Model Combination

If quality is the priority:

Reasoning:

```
qwen3-235b-a22b-thinking-2507
```

Narrative writing:

```
claude-sonnet-4-6
```

Evaluation / JSON:

```
openai-gpt-54
```

Final polish:

```
claude-opus-4-6
```

---

# Important Note on Step 7

If Step 7 output reads like isolated sentence edits instead of a coherent chapter, the issue is likely:

* the **model choice**
* the **prompt instructing sentence-level editing instead of narrative flow**

The paragraph polish step should explicitly instruct the model to:

* improve narrative flow across paragraphs
* smooth transitions
* maintain chapter coherence
* avoid unnecessary sentence-level rewrites

This step functions best as a **chapter-level editorial pass**, not a mechanical rewrite.

