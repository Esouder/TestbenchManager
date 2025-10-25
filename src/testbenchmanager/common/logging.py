from logging import Logger, LoggerAdapter
from typing import Any, MutableMapping


class PrefixAdaptor(LoggerAdapter[Any]):
    def __init__(self, logger: Logger, prefix: str):
        super().__init__(logger, {})
        self._prefix: str = prefix

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        return f"{self._prefix}{msg}", kwargs
