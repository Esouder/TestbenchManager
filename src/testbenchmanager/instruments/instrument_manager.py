import logging
from typing import Any, Optional

from testbenchmanager.instruments.physical import physical_instrument_registry
from testbenchmanager.instruments.translation import Translator, translator_registry

from .instrument_configuration import InstrumentConfiguration

logger = logging.getLogger(__name__)


class InstrumentManager:

    def __init__(self):
        self._translators: list[Translator[Any]] = []
        self.loaded_configuration_name: str | None = None
        self.loaded_configuration_description: Optional[str] = None

    def load_from_configuration(self, config: InstrumentConfiguration) -> None:

        self.stop_all_translators()

        self.loaded_configuration_name = config.name
        self.loaded_configuration_description = config.description

        physical_instrument_registry.clear()
        physical_instrument_registry.fill_from_configuration_sequence(
            config.physical_instruments
        )

        self._translators.clear()
        for translator_config in config.translators:
            try:
                translator_class = translator_registry.get(translator_config.class_name)
            except KeyError as e:
                logger.warning(
                    "Translator class '%s' not found in registry: %s",
                    translator_config.class_name,
                    e,
                )
                continue
            translator_config = translator_class.configuration().model_validate(
                translator_config.model_dump()
            )
            try:
                translator_instance = translator_class(translator_config)
                self._translators.append(translator_instance)
            except Exception as e:
                logger.error(
                    "Error occurred while instantiating translator '%s': %s",
                    translator_config.class_name,
                    e,
                )

        self.start_all_translators()

    def start_all_translators(self) -> None:
        for translator in self._translators:
            translator.start()

    def stop_all_translators(self) -> None:
        for translator in self._translators:
            translator.stop()


instrument_manager = InstrumentManager()  # global singleton instance
