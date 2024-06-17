from typing import Any

from logger.logger import DEFAULT_LOG_DIR, DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL, CallableT, Logger


def get_global_logger() -> Logger:
    return Logger.get_global_logger()


def set_global_logger(logger: Logger) -> None:
    Logger.set_global_logger(logger)


def info(msg: str, *args: Any, **kwargs: Any) -> None:
    Logger.get_global_logger().info(msg, *args, **kwargs)


def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    Logger.get_global_logger().debug(msg, *args, **kwargs)


def set_level(level: int) -> None:
    Logger.get_global_logger().set_level(level)


def warning(msg: str, *args: Any, **kwargs: Any) -> None:
    Logger.get_global_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args: Any, **kwargs: Any) -> None:
    Logger.get_global_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args: Any, exc_info: bool = True, **kwargs: Any) -> None:
    Logger.get_global_logger().exception(msg, *args, exc_info=exc_info, **kwargs)


def user(msg: str, *args: Any, **kwargs: Any) -> None:
    """Write external-facing message to log.

    This writes to both the process's configured log file as well as to user.log,
    so that we can display messages to external users easily. External messages
    should give a digestible summary of the state of the system, and avoid including
    debugging details that would not be useful to non-Metarobot folks.
    """
    Logger.get_global_logger().user(msg, *args, **kwargs)
