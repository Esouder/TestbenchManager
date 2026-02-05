"""Polling Translator implementation."""

from time import monotonic, sleep
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
)


class EntityConfiguration(BaseModel):
    """
    Configuration Model for a single output entity in the polling translator, e.g. a virtual
    instrument representing a single measurement, like a voltage or temperature.
    """

    setter_function: Optional[str] = None
    setter_arguments: dict[str, Any] = {}
    virtual_instrument: VirtualInstrumentMetadata


class PollingTranslatorConfiguration(TranslatorConfiguration):
    """
    Configuration Model for a Polling Translator (see PollingTranslator).
    """

    physical_instrument_uid: str

    getter_function: str
    getter_arguments: dict[str, Any] = {}

    polling_interval: float = 1.0  # in seconds

    # We assume that the getter will be appropriately configured to return either:
    # - a single value, which is then applied to all virtual instruments
    # - a list/tuple of values, which are then mapped to the virtual instruments in the order
    #   they are defined here.
    entities: list[EntityConfiguration] = []


@translator_registry.register_class()
class PollingTranslator(Translator[VirtualInstrumentValue]):
    """
    A polling translator has one physical instrument source, which it polls at a regular interval to
    map its output to one or more virtual instrument outputs. Each output has it's own
    entirely independent setter callbacks.

    If this is used with a one-to-many mapping of source to output instruments, it's suited
    for situations where the setter functions are called much less frequently than the polling;
    each setter (i.e. virtual instrument .command call) is handled entirely independently, no
    batching.

    But the many-to-one mapping can save a lot of overhead if the physical instrument can return
    values for multiple virtual instruments in a single call.

    It is assumed that the physical instrument's getter function is appropriately configured to
    return either a single value (applied to all virtual instruments), or a list/tuple of values
    which are then mapped to the output virtual instruments in the order they are defined in the
    configuration.

    At this time I cannot be bothered to implement more complex mapping logic like the demux BS
    the old implementation had. That was a colossal pain.

    """

    @classmethod
    def configuration(cls) -> type[PollingTranslatorConfiguration]:
        return PollingTranslatorConfiguration

    def __init__(self, configuration: PollingTranslatorConfiguration) -> None:
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

        self._polling_interval = configuration.polling_interval

        self._getter_function: Callable[[], list[VirtualInstrumentValue]] = (
            lambda: self._as_list(
                getattr(self._physical_instrument, configuration.getter_function)(
                    **configuration.getter_arguments
                )
            )
        )

        self._setter_function: Optional[Callable[[VirtualInstrumentValue], None]] = None
        for entity_config in configuration.entities:
            setter_name = entity_config.setter_function
            if setter_name is not None:
                setter_args = entity_config.setter_arguments
                self._setter_function = (
                    lambda value, _setter=setter_name, _args=setter_args: getattr(
                        self._physical_instrument, _setter
                    )(value, **_args)
                )

            virtual_instrument = VirtualInstrument(
                metadata=entity_config.virtual_instrument,
                command_callback=self._setter_function,
            )
            self.virtual_instruments[entity_config.virtual_instrument.uid] = (
                virtual_instrument
            )

    def _as_list(
        self, value: VirtualInstrumentValue | list[VirtualInstrumentValue]
    ) -> list[VirtualInstrumentValue]:
        """
        Helper method to ensure we have a list, from either a single value or a list.

        Args:
            value (VirtualInstrumentValue | list[VirtualInstrumentValue]): input, either single
            value or list of values.

        Returns:
            list[VirtualInstrumentValue]: list, either the input list, or a single-item list
            containing the input value.
        """
        if isinstance(value, list):
            return value
        return [value]

    def translation_loop(self) -> None:
        """
        Polling implementation of the translation loop.

        The core logic here is to poll the physical instrument at the configured interval,
        retrieve the values, and update the virtual instruments accordingly.

        We perform some basic checks to ensure the number of values returned matches the number
        of virtual instruments configured, and log warnings if there are any issues or we're missing
        the polling interval.
        """
        next_poll_time = monotonic() + self._polling_interval
        try:
            values = self._getter_function()
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.warning(
                "Error polling physical instrument '%s': %s",
                self._physical_instrument,
                e,
            )
            return

        if len(values) != len(self.virtual_instruments):
            self._logger.warning(
                "Polled %d values but have %d virtual instruments configured. Skipping update.",
                len(values),
                len(self.virtual_instruments),
            )
            return

        for value, virtual_instrument in zip(values, self.virtual_instruments.values()):

            try:
                virtual_instrument.update_state(value)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warning(
                    "Error updating virtual instrument '%s' state: %s",
                    virtual_instrument.metadata.uid,
                    e,
                )
        sleep_duration = next_poll_time - monotonic()
        if sleep_duration > 0:
            sleep(sleep_duration)
        else:
            # We missed the polling interval, log a warning
            self._logger.warning(
                "Polling loop missed its interval by %.3f seconds", -sleep_duration
            )
