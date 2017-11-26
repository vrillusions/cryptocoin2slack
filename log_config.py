
# -*- coding: utf-8 -*-
"""Configuration for logging."""

# idea on setting up logging:
# default level is WARN
# default level for log file is INFO
# in order for this to work:
#   set root logger to NOTSET (so all messages are processed)
#   in console handler set to WARN
#   in file handler set to INFO
# -v in script changes it to INFO
# -vv in script changes it to DEBUG
#   these options will need to modify the specific handler to actually work
# drop support of environment variable
config = {
    "version": 1,
    "root": {
        "handlers": [
            "console",
            "file",
        ],
        "level": "NOTSET",
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "WARN",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "simple",
            "level": "INFO",
            "filename": "log/cryptocoin2slack.log",
            "maxBytes": 102400,
            "backupCount": 5,
        },
    },
    "formatters": {
        "simple": {
            "format": "%(asctime)s [%(levelname)s:%(name)s] %(message)s",
        },
        "brief": {
            "format": "%(message)s",
        },
    },
}
