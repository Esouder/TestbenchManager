"""Logging utilities."""

from logging import Logger, LoggerAdapter
from typing import Any, MutableMapping


# pylint: disable=too-few-public-methods
# This is a simple adapter class. What do you want me to do?
class PrefixAdaptor(LoggerAdapter[Any]):
    """
    Implements a logging adapter that adds a prefix to log messages
    Useful for, e.g. virtual instruments to identify their log messages.
    without having to specify it in every log call.
    """

    def __init__(self, logger: Logger, prefix: str):
        super().__init__(logger, {})
        self._prefix: str = prefix

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        """
        Prepend the prefix to the log message.

        Args and Returns: See LoggerAdapter.process() documentation.
        """
        return f"{self._prefix}{msg}", kwargs
