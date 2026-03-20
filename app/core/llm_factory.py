import importlib
from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def get_llm_service():
    if settings.llm_mode == "test":
        return importlib.import_module("app.services.test_llm_service")
    elif settings.llm_mode == "prod":
        return importlib.import_module("app.services.llm_service")
    else:
        raise ValueError(f"LLM_MODE must be 'test' or 'prod', got: {settings.llm_mode}")
