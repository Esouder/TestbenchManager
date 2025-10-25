"""Factory for creating physical instrument instances from configuration."""

import importlib
import sys

from .physical_instrument_configuration import PhysicalInstrumentConfiguration


class PhysicalInstrumentFactory:
    """Factory for creating physical instrument instances from configuration.

    The typing is intentionally broad here, physical instruments can technically be any python
    object."""

    @staticmethod
    def create_instrument(
        config: PhysicalInstrumentConfiguration,
    ) -> object:
        """
        Factory method to instantiate a physical instrument (broadly, any object) from a
        configuration model.

        Args:
            config (PhysicalInstrumentConfiguration): Configuration model for the physical
            instrument.

        Raises:
            ImportError: The module specified in the configuration could not be imported.
            AttributeError: The class specified in the configuration could not be found in the module.
            RuntimeError: The instrument class could not be instantiated with the provided arguments.

        Returns:
            object: Instantiated physical instrument object.
        """
        try:
            importlib.import_module(config.module_name)
        except ImportError as e:
            raise ImportError(
                f"Failed to import module '{config.module_name}' for physical instrument "
                f"'{config.uid}': {e}"
            ) from e

        try:
            instrument_class = getattr(
                sys.modules[config.module_name], config.class_name
            )
        except AttributeError as e:
            raise AttributeError(
                f"Module '{config.module_name}' does not have a class named "
                f"'{config.class_name}' for physical instrument '{config.uid}': {e}"
            ) from e

        try:
            instrument_instance: object = instrument_class(**config.arguments)
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate physical instrument '{config.uid}' of class "
                f"'{config.class_name}' with arguments {config.arguments}: {e}"
            ) from e
        return instrument_instance
