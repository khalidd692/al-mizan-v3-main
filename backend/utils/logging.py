"""Setup logger applicatif."""

import logging
import os

def get_logger(name: str) -> logging.Logger:
    level = os.environ.get("MIZAN_LOG_LEVEL", "INFO")
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger