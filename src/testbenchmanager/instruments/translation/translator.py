"""Base class for translators."""

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
    """
    Base class for all translators. Translators are a layer in between source instruments
    (physical or virtual) and output (always virtual) instruments. They have a worker loop to
    perform the necessary logic to gather data from source instruments and update output virtual
    instruments accordingly.
    """

    def __init__(self, config: TranslatorConfiguration) -> None:
        self.metadata = config.metadata
        self._virtual_instruments: dict[
            str,
            VirtualInstrument[
                VirtualInstrumentValue
            ],  # Is there a better way to type this?
        ] = {}  # UID: VirtualInstrument mapping
        self._thread: Thread = Thread(target=self._worker_thread, daemon=True)
        self._stop_event: Event = Event()

        self._logger = PrefixAdaptor(logger, f"[{self.metadata.uid}] ")

    @classmethod
    @abstractmethod
    def configuration(cls) -> type[TranslatorConfiguration]:
        """
        Abstract method to get the configuration model associated the concrete translator
        implementation. Honestly this is a bit of a hack since you can't have abstract classmethod
        properties. Just imagine it's a property.

        Returns:
            type[TranslatorConfiguration]: Configuration Model associated with a concrete
            implementation of the Translator base class.
        """
        raise NotImplementedError()

    def start(self) -> None:
        """
        Start the translator core working loop.
        """
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the translator core working loop
        """
        self._stop_event.set()
        self._thread.join()

    def _worker_thread(self) -> None:
        """
        Core working loop, performs the necessary translation to convert from source instruments
        to output instruments.
        """
        while not self._stop_event.is_set():
            try:
                self.translation_loop()
            except Exception as e:  # pylint: disable=broad-exception-caught
                # We need to catch all exceptions here to prevent the thread from dying
                self._logger.warning("Exception raised in translation loop: %s", e)

    @abstractmethod
    def translation_loop(self) -> None:
        """
        Implementation-specific implementation to gather data from the source instruments and
        update the output virtual instruments accordingly.
        """
        raise NotImplementedError()
