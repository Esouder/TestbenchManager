"""Top-level manager for the instrumentation component."""

import logging
from dataclasses import dataclass
from typing import Any

from testbenchmanager.configuration import (
    ConfigurationDirectory,
    ConfigurationManager,
    ConfigurationScope,
)
from testbenchmanager.instruments.physical import physical_instrument_registry
from testbenchmanager.instruments.translation import Translator, translator_registry

from .instrument_configuration import (
    InstrumentConfiguration,
    InstrumentConfigurationMetadata,
)

logger = logging.getLogger(__name__)


@dataclass
class InstrumentConfigurationGroup:
    metadata: InstrumentConfigurationMetadata
    physical_instrument_uids: list[str]
    translators: list[Translator[Any]]


class InstrumentManager:
    """
    This is the top-level manager for the instrumentation component.

    It holds responsibility for populating the various instrument registries from configuration
    models, and managing the lifecycle of translators.
    """

    def inject_configuration_manager(
        self, configuration_manger: ConfigurationManager
    ) -> None:
        self._config_dir = configuration_manger.get_configuration_directory(
            ConfigurationScope.INSTRUMENTS
        )

    def __init__(self):
        self._configuration_groups: dict[str, InstrumentConfigurationGroup] = {}
        self._config_dir: ConfigurationDirectory | None = None

    @property
    def configuration_directory(self) -> ConfigurationDirectory:
        if self._config_dir is None:
            raise RuntimeError(
                "Configuration manager not injected. Cannot access configuration directory."
            )
        return self._config_dir

    def load_all_configurations(self) -> None:
        """
        Unload the current instrument configuration (if any) and load in a new instrument
        configuration.

        Args:
            config (InstrumentConfiguration): The instrument configuration model to load.
        """

        self.stop_all_translators()

        physical_instrument_registry.clear()
        self._configuration_groups = {}

        for configuration_file in self.configuration_directory.configuration_uids:
            config = InstrumentConfiguration.model_validate(
                self.configuration_directory.get_contents(configuration_file)
            )

            physical_instrument_registry.fill_from_configuration_sequence(
                config.physical_instruments
            )
            physical_instrument_uids = [
                physical_instrument.uid
                for physical_instrument in config.physical_instruments
            ]

            translators: list[Translator[Any]] = []
            for translator_config in config.translators:
                try:
                    translator_class = translator_registry.get(
                        translator_config.class_name
                    )
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
                    translators.append(translator_instance)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catching broad exception here to ensure one faulty translator does not break the
                    # entire instrument loading process. We'd like to log the error and continue.
                    logger.error(
                        "Error occurred while instantiating translator '%s': %s",
                        translator_config.class_name,
                        e,
                    )

            configuration_group = InstrumentConfigurationGroup(
                metadata=config.metadata,
                physical_instrument_uids=physical_instrument_uids,
                translators=translators,
            )

            self._configuration_groups[configuration_file] = configuration_group

        self.start_all_translators()

    def start_all_translators(self) -> None:
        """
        Start all loaded translators.
        """
        for configuration_group in self._configuration_groups.values():
            for translator in configuration_group.translators:
                translator.start()

    def stop_all_translators(self) -> None:
        """
        Stop all loaded translators.
        """
        for configuration_group in self._configuration_groups.values():
            for translator in configuration_group.translators:
                translator.stop()


instrument_manager = InstrumentManager()
