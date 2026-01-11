"""Registry for experiment steps classes."""

from testbenchmanager.common.registry import ClassRegistry

from .step import Step
from .step_configuration import StepConfiguration

step_registry = ClassRegistry[Step[StepConfiguration]]()
