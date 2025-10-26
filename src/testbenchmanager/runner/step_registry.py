# pylint: skip-file


from testbenchmanager.common.registry import ClassRegistry

from .step import Step

step_registry = ClassRegistry[Step]()
