import logging
from typing import Optional

from pydantic import BaseModel, field_validator

from .physical import PhysicalInstrumentConfiguration
from .translation import TranslatorConfiguration

logger = logging.getLogger(__name__)


class InstrumentConfiguration(BaseModel):

    name: str
    desciprtion: Optional[str] = None

    physical_instruments: list[PhysicalInstrumentConfiguration] = []

    translators: list[TranslatorConfiguration] = []

    @field_validator("physical_instruments", mode="after")
    @classmethod
    def validate_physical_instruments(
        cls,
        physical_instruments: list[PhysicalInstrumentConfiguration],
    ) -> list[PhysicalInstrumentConfiguration]:

        uids = set(
            physical_instruments_item.uid
            for physical_instruments_item in physical_instruments
        )
        if len(uids) != len(physical_instruments):
            raise ValueError(
                "Duplicate UIDs found in physical_instruments configuration."
            )
        elif len(uids) == 0:
            logger.warning("No physical instruments configured. Is this correct?")

        return physical_instruments

    @field_validator("translators", mode="after")
    @classmethod
    def validate_translators(
        cls,
        translators: list[TranslatorConfiguration],
    ) -> list[TranslatorConfiguration]:

        uids = set(translators_item.metadata.uid for translators_item in translators)
        if len(uids) != len(translators):
            raise ValueError("Duplicate UIDs found in translators configuration.")
        elif len(uids) == 0:
            logger.warning("No translators configured. Is this correct?")

        return translators
