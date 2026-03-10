from __future__ import annotations

import logging
from datetime import datetime
from logging.config import dictConfig
from zoneinfo import ZoneInfo

from uvicorn.logging import AccessFormatter, DefaultFormatter


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


class BeijingTimeMixin:
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=BEIJING_TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class BeijingDefaultFormatter(BeijingTimeMixin, DefaultFormatter):
    pass


class BeijingAccessFormatter(BeijingTimeMixin, AccessFormatter):
    pass


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "app.core.logging.BeijingDefaultFormatter",
                    "fmt": "%(asctime)s 北京时间 | %(levelprefix)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "use_colors": None,
                },
                "access": {
                    "()": "app.core.logging.BeijingAccessFormatter",
                    "fmt": "%(asctime)s 北京时间 | %(levelprefix)s %(client_addr)s - \"%(request_line)s\" %(status_code)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "use_colors": None,
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
                "app": {"handlers": ["default"], "level": "INFO", "propagate": False},
            },
            "root": {"handlers": ["default"], "level": "INFO"},
        }
    )