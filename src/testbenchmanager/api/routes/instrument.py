"""Instrument API routes"""

from bisect import bisect_left
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from testbenchmanager.api.transmission_structures import (
    InstrumentStateTransmissionStructure,
    InstrumentTransmissionStructure,
)
from testbenchmanager.instruments.virtual import (
    VirtualInstrumentState,
    VirtualInstrumentValueTypes,
    virtual_instrument_registry,
)

type StateList[T: VirtualInstrumentValueTypes] = list[VirtualInstrumentState[T]]


instrument_router = APIRouter(prefix="/instrument")


@instrument_router.get("/")
def list_instruments() -> list[str]:
    """
    List all registered instrument UIDs.

    Returns:
        list[str]: List of instrument UIDs.
    """
    return virtual_instrument_registry.keys


@instrument_router.get("/{uid}")
def get_instrument_reading(
    uid: str, sequence: Optional[int] = None, timeout: Optional[float] = None
) -> InstrumentTransmissionStructure:
    """
    Get the reading of a virtual instrument by UID.

    Args:
        uid (str): UID of the virtual instrument.
        sequence (Optional[int], optional): Optional earliest sequence to include. If this sequence is in the future, will wait until the timeout. Defaults to None.
        timeout (float, optional): timeout if waiting for a future sequence. Defaults to None, i.e. wait indefinitely.
    Returns:
        InstrumentTransmissionStructure: Transmission structure of the instrument and its states.
    """
    try:
        instrument = virtual_instrument_registry.get(uid)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    states: StateList[VirtualInstrumentValueTypes] = []
    if sequence is None:
        states = [instrument.get_latest_state()]
    else:
        try:
            instrument.wait_for(lambda s: s.sequence >= sequence, timeout=timeout)
        except TimeoutError as e:
            raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT) from e
        first_index = bisect_left(
            instrument.history, sequence, key=lambda s: s.sequence
        )
        states = instrument.history[first_index:]

    return InstrumentTransmissionStructure(
        uid=instrument.metadata.uid,
        name=instrument.metadata.name,
        unit=instrument.metadata.unit,
        description=instrument.metadata.description,
        states=[
            InstrumentStateTransmissionStructure(
                value=state.value,
                sequence=state.sequence,
                timestamp=state.timestamp,
            )
            for state in states
        ],
    )
