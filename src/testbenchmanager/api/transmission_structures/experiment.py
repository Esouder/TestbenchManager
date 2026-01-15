from pydantic import BaseModel

from testbenchmanager.experiments.experiment_configuration import ExperimentMetadata
from testbenchmanager.experiments.experiment_state import ExperimentState
from testbenchmanager.experiments.step_configuration import StepMetadata
from testbenchmanager.experiments.step_state import StepState


class ExperimentInfoTransmissionStructure(BaseModel):
    """Transmission structure for experiment information."""

    metadata: ExperimentMetadata
    steps: list[str]  # List of step UIDs


class RunInfoTransmissionStructure(BaseModel):
    """Transmission structure for experiment run information."""

    uid: str
    experiment_metadata: ExperimentMetadata
    state: ExperimentState
    start_time: str | None = None
    end_time: str | None = None


class StepInfoTransmissionStructure(BaseModel):
    """Transmission structure for step information."""

    metadata: StepMetadata
    state: StepState
    start_time: str | None = None
    end_time: str | None = None
