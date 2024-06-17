import logging
import os
import threading
import traceback
from collections import OrderedDict
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import attr
from pythonjsonlogger import jsonlogger

# Settings for normal text logs
DEFAULT_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
DEFAULT_LOG_FORMAT = "[%(name)s] %(asctime)s - %(threadName)-8s - %(levelname)-4s %(message)s"
DEFAULT_LOG_DIR = os.environ.get("LOG_DIR") or r"/home/gort/rms-log"  # "/home/henry/log/metabot-rms"

# Settings for json logs
# Fields to include for JSON log records (from https://docs.python.org/3/library/logging.html#logrecord-attributes)
DEFAULT_JSON_FIELDS_TO_INCLUDE = {
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "name",
    "process",
    "processName",
    "thread",
    "threadName",
}

# Settings for log rotation (rotate logs once per day with 7 days of backups)
LOG_ROTATION_TIME_UNITS = "W0"  # Rotate on Mondays at midnight
LOG_ROTATION_NUM_BACKUPS = 12

DEFAULT_USER_LOG_FORMAT = "%(asctime)s %(message)s"

# custom logging levels

# set level of TIMING to be between INFO and DEBUG
LEVEL_TIMING = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(LEVEL_TIMING, "TIMING")

# set USER to be the highest level
LEVEL_USER = logging.CRITICAL + 10
logging.addLevelName(LEVEL_USER, "USER")

CallableT = TypeVar("CallableT", bound=Callable[..., Any])


@attr.s(kw_only=True)
class TimingsManager:
    timing_levels: List[str] = attr.ib(factory=list)
    timings: Dict[str, List[float]] = attr.ib(factory=OrderedDict)
    timing_parent_to_children: Dict[str, List[str]] = attr.ib(factory=dict)
    timing_child_to_parent: Dict[str, str] = attr.ib(factory=dict)
    timing_root_keys: List[str] = attr.ib(factory=list)

    def clear(self) -> None:
        self.timings.clear()
        self.timing_parent_to_children.clear()
        self.timing_child_to_parent.clear()
        self.timing_root_keys.clear()


def _make_stream_handler(log_level: int, log_format: str) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    return handler


def _make_timed_rotation_handler(log_path: str, log_level: int, formatter: logging.Formatter) -> logging.Handler:
    handler = TimedRotatingFileHandler(
        log_path,
        encoding="utf-8",
        when=LOG_ROTATION_TIME_UNITS,
        backupCount=LOG_ROTATION_NUM_BACKUPS,
    )
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    return handler


class Logger:
    _global_logger: Optional["Logger"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        name: Optional[str] = None,
        log_level: Union[str, int] = DEFAULT_LOG_LEVEL,
        log_format: str = DEFAULT_LOG_FORMAT,
        log_dir: str = DEFAULT_LOG_DIR,
    ):
        log_level = getattr(logging, log_level.upper()) if isinstance(log_level, str) else log_level

        self._logger = logging.getLogger(name)
        self._logger.handlers.clear()
        self._logger.setLevel(log_level)
        self._log_timing = True
        self._suppress_timing_msg = False

        # Add a default handler for logging to stdout
        self._logger.addHandler(_make_stream_handler(log_level, log_format))

        if name is None:
            # This mainly happens inside multiprocessing-launched processes, or else if there's an
            # entry point that failed to configure its logging name.
            self._logger.warning("No logger name was given! Logs will not be saved. ")
            return

        if not os.path.exists(log_dir):
            self._logger.warning(f"Logging dir '{log_dir}' doesn't exist! Logs will not be saved.")
            return

        # Add a handler for normal text logs
        text_log_path = os.path.join(log_dir, f"{name}.log")
        self._logger.info(f"Writing text logs to {text_log_path}")

        self._logger.addHandler(_make_timed_rotation_handler(text_log_path, log_level, logging.Formatter(log_format)))

        # user.log will capture USER-level log lines
        # user.log can be used across different logger instances/Python instances/processes
        # because POSIX guarantees that appends from multiple processes will work, more or less:
        # https://nullprogram.com/blog/2016/08/03/
        user_log_path = os.path.join(log_dir, "user.log")
        self._logger.info(f"Writing user logs to {user_log_path}")
        self._logger.addHandler(
            _make_timed_rotation_handler(user_log_path, LEVEL_USER, logging.Formatter(DEFAULT_USER_LOG_FORMAT))
        )

        # Add a handler for JSON logs as JSON lines (.jsonl)
        json_log_path = os.path.join(log_dir, f"{name}.jsonl")
        self._logger.info(f"Writing json logs to {json_log_path}")
        reserved_attrs = list(set(jsonlogger.RESERVED_ATTRS) - DEFAULT_JSON_FIELDS_TO_INCLUDE)
        json_formatter = jsonlogger.JsonFormatter(
            timestamp=True, reserved_attrs=reserved_attrs, json_ensure_ascii=False
        )
        self._logger.addHandler(_make_timed_rotation_handler(json_log_path, log_level, json_formatter))

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def set_level(self, level: int) -> None:
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            handler.setLevel(level)

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        for handler in self._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        self._logger.handlers.clear()

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        try:
            if self._logger.isEnabledFor(level):
                self._logger.log(level, msg, *args, **kwargs)
        except Exception as e:
            if isinstance(e, NameError):
                pass
            else:
                traceback.print_exc()

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, exc_info: bool = True, **kwargs: Any) -> None:
        self.log(logging.ERROR, msg, *args, exc_info=exc_info, **kwargs)

    def user(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Write external-facing message to log.

        This writes to both the process's configured log file as well as to user.log,
        so that we can display messages to external users easily. External messages
        should give a digestible summary of the state of the system, and avoid including
        debugging details that would not be useful to non-Metarobot folks.
        """
        self.log(LEVEL_USER, msg, *args, **kwargs)

    def _timing_msg(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.log(LEVEL_TIMING, msg, *args, **kwargs)

    @staticmethod
    def get_global_logger() -> "Logger":
        if Logger._global_logger is None:
            Logger._global_logger = Logger()
        return Logger._global_logger

    @staticmethod
    def set_global_logger(logger: "Logger") -> None:
        with Logger._lock:
            if Logger._global_logger is not None:
                Logger._global_logger.close()
            Logger._global_logger = logger
