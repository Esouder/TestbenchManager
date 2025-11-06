"""Registry for translator classes."""

from typing import Any

from testbenchmanager.common.registry import ClassRegistry

from .translator import Translator

translator_registry = ClassRegistry[Translator[Any]]()
