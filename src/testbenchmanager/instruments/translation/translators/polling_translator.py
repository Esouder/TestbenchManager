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
    virtual_instrument_registry,
)


class EntityConfiguration(BaseModel):
    setter_function: Optional[str] = None
    setter_arguments: dict[str, Any] = {}
    virtual_instrument: VirtualInstrumentMetadata


class PollingTranslatorConfiguration(TranslatorConfiguration):
    physical_instrument_uid: str

    getter_function: str
    getter_arguments: dict[str, Any] = {}

    polling_interval: float = 1.0  # in seconds

    # We assume that the getter is set up return either:
    # - a single value, which is then applied to all virtual instruments
    # - a list/tuple of values, which are then mapped to the virtual instruments in the order
    #   they are defined here.
    entities: list[EntityConfiguration] = []


@translator_registry.register_class()
class PollingTranslator(Translator[VirtualInstrumentValue]):

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
            self._virtual_instruments[entity_config.virtual_instrument.uid] = (
                virtual_instrument
            )
            try:
                virtual_instrument_registry.register(
                    entity_config.virtual_instrument.uid, virtual_instrument
                )
            except KeyError as e:
                self._logger.warning(
                    "Failed to register virtual instrument with UID '%s': %s",
                    entity_config.virtual_instrument.uid,
                    e,
                )

    def _as_list(
        self, value: VirtualInstrumentValue | list[VirtualInstrumentValue]
    ) -> list[VirtualInstrumentValue]:
        if isinstance(value, list):
            return value
        return [value]

    def translation_loop(self) -> None:
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

        if len(values) != len(self._virtual_instruments):
            self._logger.warning(
                "Polled %d values but have %d virtual instruments configured. Skipping update.",
                len(values),
                len(self._virtual_instruments),
            )
            return

        for value, virtual_instrument in zip(
            values, self._virtual_instruments.values()
        ):

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
