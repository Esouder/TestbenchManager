from datetime import datetime

from pydantic import BaseModel

from testbenchmanager.experiments.experiment_configuration import ExperimentMetadata
from testbenchmanager.experiments.state import Outcome, State
from testbenchmanager.experiments.step_configuration import StepMetadata


class StepConfigurationTransmissionStructure(BaseModel):
    """Transmission structure for step configuration."""

    metadata: StepMetadata
    skip_on_previous_failure: bool
    skip_on_abort: bool


class ExperimentConfigurationTransmissionStructure(BaseModel):
    """Transmission structure for experiment configuration."""

    metadata: ExperimentMetadata
    steps: dict[str, StepConfigurationTransmissionStructure]


class ExperimentRunTransmissionStructure(BaseModel):
    """Transmission structure for experiment run."""

    configuration_uid: str
    state: State
    outcome: Outcome | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class StepRunTransmissionStructure(BaseModel):
    """Transmission structure for step run."""

    confguration_uid: str
    state: State
    outcome: Outcome | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
