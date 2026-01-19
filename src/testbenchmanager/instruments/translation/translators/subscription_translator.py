"""Subscription Translator implementation."""

from typing import Any, Callable, Optional

from pydantic import BaseModel

from testbenchmanager.instruments.physical import physical_instrument_registry
from testbenchmanager.instruments.translation import (
    Translator,
    TranslatorConfiguration,
    translator_registry,
)
from testbenchmanager.instruments.virtual import (
    VirtualInstrument,
    VirtualInstrumentMetadata,
    VirtualInstrumentValue,
    virtual_instrument_registry,
)


class EntityConfiguration(BaseModel):
    """
    Configuration Model for a single output entity in the subscription translator.

    Attributes:
        extractor_field: Optional attribute/field name to extract from the subscription message.
            For simple field extraction (e.g., state.pressure), specify this instead of
            extractor_function. Supports dot notation for nested attributes (e.g., "meta.version").
        extractor_function: Optional name of a method to call on the physical instrument
            to transform the subscription message. If both extractor_field and extractor_function
            are None, the entire message is used as the value.
        extractor_arguments: Additional keyword arguments to pass to the extractor function.
        setter_function: Optional name of a function to call when a command is sent to this
            virtual instrument.
        setter_arguments: Additional keyword arguments to pass to the setter function.
        virtual_instrument: Metadata for the virtual instrument this entity maps to.
    """

    extractor_field: Optional[str] = None
    extractor_function: Optional[str] = None
    extractor_arguments: dict[str, Any] = {}
    setter_function: Optional[str] = None
    setter_arguments: dict[str, Any] = {}
    virtual_instrument: VirtualInstrumentMetadata

@translator_registry.register_class()
class SubscriptionTranslatorConfiguration(TranslatorConfiguration):
    """
    Configuration Model for a Subscription Translator.

    Subscription translators work with physical instruments that push data asynchronously
    (e.g., via callbacks/subscribers) rather than pulling data on demand. This is ideal for
    sensors that continuously emit data or have event-driven updates.

    Attributes:
        physical_instrument_uid: UID of the physical instrument providing the subscription.
        subscribe_function: Name of the method on the physical instrument to call to register
            a subscription callback.
        entities: List of output entities (virtual instruments) and their mappings.
    """

    physical_instrument_uid: str
    subscribe_function: str
    entities: list[EntityConfiguration] = []


@translator_registry.register_class()
class SubscriptionTranslator(Translator[VirtualInstrumentValue]):
    """
    A subscription translator listens to a physical instrument that provides data via
    callbacks/subscriptions and maps that data to one or more virtual instruments.

    This translator is suitable for:
    - Sensors that continuously emit data (e.g., vacuum gauges, temperature sensors)
    - Event-driven instruments that push updates asynchronously
    - Many-to-one mappings where a single subscription provides data for multiple outputs

    The subscription message is passed to optional extractor functions that can parse
    or transform the data before it's assigned to virtual instruments. Each virtual
    instrument can have an independent extractor and setter.

    Example use cases:
    - InficonBGP400 vacuum gauge that pushes pressure/status updates
    - DAQ devices that stream sensor data
    - IoT sensors with live telemetry
    """

    @classmethod
    def configuration(cls) -> type[SubscriptionTranslatorConfiguration]:
        return SubscriptionTranslatorConfiguration

    def __init__(self, configuration: SubscriptionTranslatorConfiguration) -> None:
        super().__init__(configuration)

        try:
            self._physical_instrument = physical_instrument_registry.get(
                configuration.physical_instrument_uid
            )
        except KeyError as e:
            raise RuntimeError(
                f"Physical instrument with UID "
                f"'{configuration.physical_instrument_uid}' not found in registry."
            ) from e

        # Build extractors and setters for each entity
        self._entity_configs = configuration.entities
        self._extractors: dict[str, Callable[[Any], VirtualInstrumentValue]] = {}
        self._setters: dict[str, Optional[Callable[[VirtualInstrumentValue], None]]] = (
            {}
        )

        for entity_config in self._entity_configs:
            virtual_instrument_uid = entity_config.virtual_instrument.uid

            # Build extractor function
            if entity_config.extractor_field is not None:
                # Direct field extraction using dot notation
                field_path = entity_config.extractor_field
                self._extractors[virtual_instrument_uid] = (
                    lambda value, _field=field_path: self._extract_field(value, _field)
                )
            elif entity_config.extractor_function is not None:
                # Custom extractor function on physical instrument
                extractor_name = entity_config.extractor_function
                extractor_args = entity_config.extractor_arguments
                self._extractors[virtual_instrument_uid] = (
                    lambda value, _extractor=extractor_name, _args=extractor_args: getattr(
                        self._physical_instrument, _extractor
                    )(
                        value, **_args
                    )
                )
            else:
                # No extractor, use the entire message
                self._extractors[virtual_instrument_uid] = lambda value: value

            # Build setter function
            if entity_config.setter_function is not None:
                setter_name = entity_config.setter_function
                setter_args = entity_config.setter_arguments
                self._setters[virtual_instrument_uid] = (
                    lambda value, _setter=setter_name, _args=setter_args: getattr(
                        self._physical_instrument, _setter
                    )(value, **_args)
                )
            else:
                self._setters[virtual_instrument_uid] = None

            # Create and register virtual instrument
            virtual_instrument = VirtualInstrument(
                metadata=entity_config.virtual_instrument,
                command_callback=self._setters[virtual_instrument_uid],
            )
            self._virtual_instruments[virtual_instrument_uid] = virtual_instrument
            try:
                virtual_instrument_registry.register(
                    virtual_instrument_uid, virtual_instrument
                )
            except KeyError as e:
                self._logger.warning(
                    "Failed to register virtual instrument with UID '%s': %s",
                    virtual_instrument_uid,
                    e,
                )

        # Register the subscription callback with the physical instrument
        subscribe_function_name = configuration.subscribe_function
        subscribe_function = getattr(self._physical_instrument, subscribe_function_name)
        self._unsubscribe = subscribe_function(self._on_subscription_update)

    def _extract_field(self, obj: Any, field_path: str) -> VirtualInstrumentValue:
        """
        Extract a field from an object using dot notation.

        Supports nested attribute access, e.g., "state.nested.field".

        Args:
            obj: The object to extract from.
            field_path: Dot-separated field path (e.g., "pressure" or "meta.version").

        Returns:
            VirtualInstrumentValue: The extracted field value.

        Raises:
            AttributeError: If the field path cannot be resolved.
        """
        current = obj
        for field in field_path.split("."):
            current = getattr(current, field)
        return current

    def _on_subscription_update(self, message: Any) -> None:
        """
        Callback invoked when the physical instrument pushes an update.

        This method is called by the physical instrument's subscription mechanism.
        It extracts values from the message and updates the corresponding virtual instruments.

        Args:
            message: The message/state object from the physical instrument.
        """
        for (
            virtual_instrument_uid,
            virtual_instrument,
        ) in self._virtual_instruments.items():
            try:
                extractor = self._extractors[virtual_instrument_uid]
                value = extractor(message)
                virtual_instrument.update_state(value)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warning(
                    "Error updating virtual instrument '%s' from subscription message: %s",
                    virtual_instrument_uid,
                    e,
                )

    def translation_loop(self) -> None:
        """
        For subscription-based translators, the worker thread simply waits without
        doing anything, since all updates are driven by the subscription callback.

        We could potentially add housekeeping logic here in the future (e.g., heartbeat
        checks, timeout detection), but for now the translator is purely callback-driven.
        """
        # The subscription mechanism is event-driven; nothing to do in this loop.
        # The _on_subscription_update callback handles all the work.
        # We just sleep to prevent spinning and let the event loop handle updates.
        import time

        time.sleep(0.1)
