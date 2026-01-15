import csv
from multiprocessing import Event
from pathlib import Path
from types import TracebackType
from typing import Annotated, Any, Callable

from pydantic import BaseModel, Field

from testbenchmanager.instruments.virtual.virtual_instrument import (
    VirtualInstrument,
    VirtualInstrumentValue,
)

from .datapoint import DataPoint
from .report_metadata import ReportMetadata

#TODO: experiment configuration reporting


class ReportManifest(BaseModel):
    def __init__(self, working_directory: Path, **data: Any):
        data_directory = working_directory / "data"
        log_directory = working_directory / "logs"
        super().__init__(**data, working_directory=working_directory, data_directory=data_directory, log_directory=log_directory)

    
    manifest: Path = Path("manifest.json")
    metadata: Path = Path("metadata.json")
    #experiment_config: Path
    data: dict[str, Path] = {} # instrument UID, path to data file
    logs: dict[str, Path] = {} # log type, path to log file

    working_directory: Annotated[Path, Field(exclude=True)]
    data_directory: Annotated[Path, Field(exclude=True)]
    log_directory: Annotated[Path, Field(exclude=True)]

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        with open(self.working_directory / self.manifest, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

class Report:

    def __init__(self, base_working_directory: Path, metadata: ReportMetadata, publish_callbacks: list[Callable[["Report"], None ]] = []):
        self._closed = Event()
        self._publish_callbacks = publish_callbacks
        self.metadata = metadata

        
        working_directory = base_working_directory / metadata.uid
        if working_directory.exists():
            raise FileExistsError(f"Report directory {working_directory} already exists.")

        try:
            working_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"Could not create report working directory {working_directory}: {e}") from e
        
        self.manifest = ReportManifest(working_directory)
        
        try:
            self.manifest.data_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"Could not create data directory {self.manifest.working_directory}: {e}") from e
        try:
            self.manifest.log_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"Could not create logs directory {self.manifest.log_directory}: {e}") from e

        with open(self.manifest.working_directory / self.manifest.metadata, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=4))
        # if self.manifest.experiment_config and experiment_config:
        #     with open(self.manifest.working_directory / self.manifest.experiment_config, "w", encoding="utf-8") as f:
        #         f.write(experiment_config.model_dump_json(indent=4))        
    

    def new_data_point(self, instrument_uid: str, datapoint: DataPoint[Any]):
        if self.closed:
            raise RuntimeError("Cannot add data point to closed report.")
        if instrument_uid not in self.manifest.data:
            data_file_path = self.manifest.data_directory / f"{instrument_uid}_data.csv"
            with open(data_file_path, "w", encoding="utf-8") as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(["timestamp", "value"])
            with self.manifest as manifest:
                manifest.data[instrument_uid] = data_file_path
        else:
            data_file_path = self.manifest.data[instrument_uid]
        with open(data_file_path, "a", encoding="utf-8") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow([datapoint.timestamp.isoformat(), datapoint.value])

    def subscribe_to_instrument(self, instrument: VirtualInstrument[VirtualInstrumentValue]):     
        instrument.subscribe(
            lambda state: self.new_data_point(
                instrument.metadata.uid,
                DataPoint(timestamp=state.timestamp, value=state.value)
            )
        )

    def close(self):
        self._closed.set()
        for callback in self._publish_callbacks:
            callback(self)

    @property
    def closed(self) -> bool:
        return self._closed.is_set()
