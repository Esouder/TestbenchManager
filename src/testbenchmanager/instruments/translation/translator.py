import logging
from abc import ABC, abstractmethod
from threading import Event, Thread
from typing import Generic

from testbenchmanager.common.logging import PrefixAdaptor
from testbenchmanager.instruments.virtual import (
    VirtualInstrument,
    VirtualInstrumentValue,
)

from .translator_configuration import TranslatorConfiguration

logger = logging.getLogger(__name__)


class Translator(ABC, Generic[VirtualInstrumentValue]):
    def __init__(self, config: TranslatorConfiguration) -> None:
        self.metadata = config.metadata
        self._virtual_instruments: dict[
            str,
            VirtualInstrument[
                VirtualInstrumentValue
            ],  # Is there a better way to type this?
        ]  # UID: VirtualInstrument mapping = {}
        self._thread: Thread = Thread(target=self.worker_thread, daemon=True)
        self._stop_event: Event = Event()

        self._logger = PrefixAdaptor(logger, f"[{self.metadata.uid}] ")

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join()

    def worker_thread(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.translation_loop()
            except Exception as e:  # pylint: disable=broad-exception-caught
                # We need to catch all exceptions here to prevent the thread from dying
                self._logger.warning("Exception raised in translation loop: %s", e)

    @abstractmethod
    def translation_loop(self) -> None: ...
