from pydantic import BaseModel

from testbenchmanager.common.registry import ClassRegistry

from .report_publisher import ReportPublisher

report_publisher_registry = ClassRegistry[ReportPublisher[BaseModel]]()
