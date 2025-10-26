"""Virtual instrument submodule."""

from .virtual_instrument import VirtualInstrument as VirtualInstrument
from .virtual_instrument import VirtualInstrumentMetadata as VirtualInstrumentMetadata
from .virtual_instrument_registry import (
    virtual_instrument_registry as virtual_instrument_registry,
)
from .virtual_instrument_state import VirtualInstrumentState as VirtualInstrumentState
from .virtual_instrument_state import VirtualInstrumentValue as VirtualInstrumentValue
