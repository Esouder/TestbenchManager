
from pydantic import BaseModel

from .report import Report, ReportMetadata
from .report_configuartion import ReportConfiguration
from .report_publisher import ReportPublisher
from .report_publisher_registry import report_publisher_registry


class ReportManager:
    def __init__(self, configuration: ReportConfiguration):
        #TODO: some try/catch in here
        self._base_working_directory = configuration.working_directory
        self._publishers: list[ReportPublisher[BaseModel]] = []
        for publisher_name, publisher_config in configuration.publishers.items():
            publisher_cls = report_publisher_registry.get(publisher_name)
            if not publisher_cls:
                raise ValueError(f"Unknown report publisher: {publisher_name}")
            config = publisher_cls.config().model_validate(publisher_config)
            publisher = publisher_cls(config)
            self._publishers.append(publisher)

    def generate_report(self, metadata: ReportMetadata) -> Report:
        publish_callbacks = [publisher.publish for publisher in self._publishers]
        return Report(self._base_working_directory, metadata, publish_callbacks)
    
    


    


