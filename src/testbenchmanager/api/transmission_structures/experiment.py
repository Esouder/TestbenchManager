from pydantic import BaseModel

from testbenchmanager.experiments.experiment_state import ExperimentState
from testbenchmanager.experiments.step_state import StepState


class ExperimentInfoTransmissionStructure(BaseModel):
    """Transmission structure for experiment information."""

    uid: str
    name: str
    description: str | None = None
    steps: list[str]  # List of step UIDs


class RunInfoTransmissionStructure(BaseModel):
    """Transmission structure for experiment run information."""

    uid: str
    experiment_uid: str
    state: ExperimentState
    start_time: str | None = None
    end_time: str | None = None


class StepInfoTransmissionStructure(BaseModel):
    """Transmission structure for step information."""

    uid: str
    name: str | None = None
    state: StepState
    start_time: str | None = None
    end_time: str | None = None
