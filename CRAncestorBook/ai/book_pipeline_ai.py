# book_pipeline_ai.py

from pathlib import Path
from typing import Any

from WrapAI import ProviderConfig
from WrapAI import get_provider_instance
from WrapAI import PromptLibrary
from WrapAI.utils.secret_loader import load_secret

from CRAncestorBook.core import (
    DEFAULT_MODEL,
    DEFAULT_PROMPT_JSON,
    DEFAULT_PROVIDER,
    PROVIDER_API_KEYS,
)

import logging

# Logger Configuration
logger = logging.getLogger(__name__)

def load_prompt_library(prompt_json: Path | None = None) -> PromptLibrary:
    return PromptLibrary.from_json_file(str(prompt_json or DEFAULT_PROMPT_JSON))


def build_runner(*, ai_model: str | None = None, provider_name: str | None = None) -> Any:
    """
    Build a provider-backed runner (OpenAI or Venice).

    - provider_name: overrides DEFAULT_PROVIDER when provided
    - ai_model: overrides DEFAULT_MODEL when provided
    """
    provider = provider_name or DEFAULT_PROVIDER
    model = ai_model or DEFAULT_MODEL

    logger.info(f"Building runner: provider={provider}, model={model}")

    if provider not in PROVIDER_API_KEYS:
        raise ValueError(f"Unknown provider key: {provider!r}")

    api_key_name = PROVIDER_API_KEYS[provider]
    api_key = load_secret(api_key_name)

    if not api_key:
        raise RuntimeError(
            f"Missing API key: environment variable '{api_key_name}' is not set."
        )

    config = ProviderConfig(
        name=provider,
        api_key=api_key,
        default_model=model,
    )

    # Provider instance (wraps a text prompt runner as .client)
    prov = get_provider_instance(config.name, config.api_key, config.default_model)

    # Return the underlying runner used by your pipeline (has set_attributes/prompt/stream methods)
    return prov.get_text_prompt_runner()


def pick_model(override: str | None, *, fallback: str | None = None) -> str:
    """
    Choose a model for a step/substep.
    - override wins if provided
    - else fallback if provided
    - else DEFAULT_MODEL
    """
    return override or fallback or DEFAULT_MODEL
