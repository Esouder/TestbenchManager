from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

from pydantic import BaseModel

from testbenchmanager.configuration import (
    ConfigurationDirectory,
    ConfigurationManager,
    ConfigurationScope,
)

from .report import Report, ReportMetadata
from .report_configuartion import ReportConfiguration, ReportConfigurationMetadata
from .report_publisher import ReportPublisher
from .report_publisher_registry import report_publisher_registry

logger = getLogger(__name__)


@dataclass
class ReportConfigurationGroup:
    metadata: ReportConfigurationMetadata
    base_working_directory: Path | None
    publishers: list[ReportPublisher[BaseModel]]


class ReportManager:
    def __init__(self) -> None:
        self._base_working_directory: Path | None = None
        self._config_dir: ConfigurationDirectory | None = None
        self._configuration_groups: dict[str, ReportConfigurationGroup] = {}

    def inject_configuration_manager(
        self,
        configuration_manager: ConfigurationManager,
    ) -> None:
        self._config_dir = configuration_manager.get_configuration_directory(
            ConfigurationScope.REPORTS
        )

    @property
    def publishers(self) -> list[ReportPublisher[BaseModel]]:
        if not self._configuration_groups:
            raise RuntimeError(
                "No report configuration groups loaded, cannot access publishers."
            )
        all_publishers: list[ReportPublisher[BaseModel]] = []
        for group in self._configuration_groups.values():
            all_publishers.extend(group.publishers)
        return all_publishers

    @property
    def base_working_directory(self) -> Path:
        if self._base_working_directory is None:
            raise RuntimeError(
                "No base working directory specified, cannot generate reports."
            )
        return self._base_working_directory

    @property
    def configuration_directory(self) -> ConfigurationDirectory:
        if self._config_dir is None:
            raise RuntimeError(
                "Configuration manager not injected. Cannot access configuration directory."
            )
        return self._config_dir

    def load_all_configurations(self):
        # TODO: some try/catch in here
        self._configuration_groups = {}
        self._base_working_directory = None
        for configuration_file in self.configuration_directory.configuration_uids:
            config = ReportConfiguration.model_validate(
                self.configuration_directory.get_contents(configuration_file)
            )

            publishers: list[ReportPublisher[BaseModel]] = []
            for publisher_name, publisher_config_data in config.publishers.items():
                publisher_cls = report_publisher_registry.get(publisher_name)
                if not publisher_cls:
                    raise ValueError(f"Unknown report publisher: {publisher_name}")
                publisher_config = publisher_cls.config().model_validate(
                    publisher_config_data
                )
                publisher = publisher_cls(publisher_config)
                publishers.append(publisher)

            config_group = ReportConfigurationGroup(
                metadata=config.metadata,
                base_working_directory=config.working_directory,
                publishers=publishers,
            )
            if (
                self._base_working_directory is not None
                and self._base_working_directory != config_group.base_working_directory
            ):
                logger.warning(
                    "Overriding existing report base working directory '%s' with new value from configuration '%s': %s",
                    self._base_working_directory,
                    configuration_file,
                    config_group.base_working_directory,
                )
            self._base_working_directory = config.working_directory
            logger.debug(
                "Set report base working directory to: %s",
                self._base_working_directory,
            )

            self._configuration_groups[configuration_file] = config_group

    def generate_report(self, metadata: ReportMetadata) -> Report:
        publish_callbacks = [publisher.publish for publisher in self.publishers]
        return Report(self.base_working_directory, metadata, publish_callbacks)


report_manager = ReportManager()  # global singleton instance
