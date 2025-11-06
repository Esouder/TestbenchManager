"""Virtual Instrument State definition."""

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

type VirtualInstrumentValueTypes = int | float | str | bool
VirtualInstrumentValue = TypeVar(
    "VirtualInstrumentValue", bound=VirtualInstrumentValueTypes
)


@dataclass
class VirtualInstrumentState(Generic[VirtualInstrumentValue]):
    """State of a Virtual Instrument at a given point in time."""

    value: VirtualInstrumentValue  # Value of the instrument
    sequence: int  # Sequence number of the state update
    timestamp: datetime  # Timestamp of when the state was recorded
