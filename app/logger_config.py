import logging
import logging.config
import os

from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"},
        "file": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | pid:%(process)d tid:%(thread)d | %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "file",
        },
    },
    "root": {"handlers": ["console", "file"], "level": LOG_LEVEL},
    "loggers": {
        "uvicorn.error": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}


def configure_logging():
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
