"""Registry for physical instruments."""

import logging
from typing import Sequence

from testbenchmanager.common.registry import Registry

from .physical_instrument_configuration import PhysicalInstrumentConfiguration
from .physical_instrument_factory import PhysicalInstrumentFactory

logger = logging.getLogger(__name__)


class PhysicalInstrumentRegistry(Registry[object]):
    """
    Registry for physical instruments.
    """

    def fill_from_configuration_sequence(
        self, configs: Sequence[PhysicalInstrumentConfiguration]
    ) -> None:
        """
        Populate the registry from a sequence of physical instrument configuration models.

        Args:
            configs (Sequence[PhysicalInstrumentConfiguration]): Sequence of physical instrument
            configuration models.
        """
        for config in configs:
            try:
                physical_instrument = PhysicalInstrumentFactory.create_instrument(
                    config
                )
            except (ImportError, RuntimeError, AttributeError) as e:
                logger.warning(
                    "Failed to create physical instrument with UID '%s': %s",
                    config.uid,
                    e,
                )
                continue
            try:
                self.register(config.uid, physical_instrument)
            except KeyError as e:
                logger.warning(
                    "Failed to register physical instrument with UID '%s': %s",
                    config.uid,
                    e,
                )

    def clear(self) -> None:
        """
        Clear all registered physical instruments.
        """
        self._registry.clear()


physical_instrument_registry = Registry[object]()  # global singleton instance
