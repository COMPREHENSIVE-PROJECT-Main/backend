import logging
import os
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    llm_mode = os.getenv("LLM_MODE", "")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if llm_mode:
            fmt = f"[%(asctime)s] [%(levelname)s] [%(name)s] [LLM_MODE: {llm_mode}] %(message)s"
        else:
            fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
