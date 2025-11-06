"""Instrument transmission structures"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from testbenchmanager.instruments.virtual import VirtualInstrumentValueTypes


class InstrumentStateTransmissionStructure(BaseModel):
    """Transmission structure for a single instrument state."""

    value: VirtualInstrumentValueTypes
    sequence: int
    timestamp: datetime


class InstrumentTransmissionStructure(BaseModel):
    """Transmission structure for an instrument and its states."""

    uid: str
    name: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    states: list[InstrumentStateTransmissionStructure]
