"""configuration model definitions for the instruments-scope configuration file."""

import logging
from typing import Optional

from pydantic import BaseModel, field_validator

from testbenchmanager.instruments.physical.physical_instrument_configuration import (
    PhysicalInstrumentConfiguration,
)
from testbenchmanager.instruments.translation.translator_configuration import (
    TranslatorConfiguration,
)

logger = logging.getLogger(__name__)


class InstrumentConfiguration(BaseModel):
    """
    Configuration model for the instrument-scope config file.
    """

    name: str
    description: Optional[str] = None

    physical_instruments: list[PhysicalInstrumentConfiguration] = []

    translators: list[TranslatorConfiguration] = []

    @field_validator("physical_instruments", mode="after")
    @classmethod
    def validate_physical_instruments(
        cls,
        physical_instruments: list[PhysicalInstrumentConfiguration],
    ) -> list[PhysicalInstrumentConfiguration]:
        """
        Perform validation on elements of the physical instrument list.
        """

        uids = set(
            physical_instruments_item.uid
            for physical_instruments_item in physical_instruments
        )
        if len(uids) != len(physical_instruments):
            raise ValueError(
                "Duplicate UIDs found in physical_instruments configuration."
            )
        if len(uids) == 0:
            logger.warning("No physical instruments configured. Is this correct?")

        return physical_instruments

    @field_validator("translators", mode="after")
    @classmethod
    def validate_translators(
        cls,
        translators: list[TranslatorConfiguration],
    ) -> list[TranslatorConfiguration]:
        """
        Perform validation on elements of the translators list.
        """

        uids = set(translators_item.metadata.uid for translators_item in translators)
        if len(uids) != len(translators):
            raise ValueError("Duplicate UIDs found in translators configuration.")
        if len(uids) == 0:
            logger.warning("No translators configured. Is this correct?")

        return translators
