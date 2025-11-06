# pylint: skip-file
# TODO: Remove skip-file when possible


from testbenchmanager.common.registry import ClassRegistry

from .step import Step

step_registry = ClassRegistry[Step]()
