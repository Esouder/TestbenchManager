import shutil
from pathlib import Path

from pydantic import BaseModel

from testbenchmanager.report_generator.report import Report
from testbenchmanager.report_generator.report_publisher_registry import (
    report_publisher_registry,
)


class LocalArchiveConfiguration(BaseModel):
    storage_path: Path

@report_publisher_registry.register_class()
class LocalArchivePublisher:
    def __init__(self, config: LocalArchiveConfiguration):
        self._storage_path: Path = config.storage_path

    @classmethod
    def config(cls) -> type[LocalArchiveConfiguration]:
        return LocalArchiveConfiguration

    def publish(self, report: Report) -> None:
        Path(self._storage_path).mkdir(parents=True, exist_ok=True)
        shutil.make_archive(
            str(Path(self._storage_path) / report.metadata.uid),
            'zip',
            report.manifest.working_directory
        )