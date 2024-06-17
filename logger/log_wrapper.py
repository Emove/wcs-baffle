from typing import Any

import logger


class LogWrapper:
    """
    Simple wrapper class to allow for adding useful class or module name prefixes to logs.
    """

    def __init__(self, prefix: str):
        self._prefix = f"[{prefix}] "

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        logger.info(f"{self._prefix}{msg}", *args, *kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        logger.warning(f"{self._prefix}{msg}", *args, *kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        logger.error(f"{self._prefix}{msg}", *args, *kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        logger.exception(f"{self._prefix}{msg}", *args, *kwargs)
