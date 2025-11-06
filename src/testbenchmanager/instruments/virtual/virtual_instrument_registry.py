"""Registry for Virtual Instruments."""

from typing import Any

from testbenchmanager.common.registry import Registry

from .virtual_instrument import VirtualInstrument

virtual_instrument_registry = Registry[VirtualInstrument[Any]]()
