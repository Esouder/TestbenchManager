from typing import Annotated

from pydantic import BaseModel, Field

from .step_configuration import StepConfiguration


class ExperimentMetadata(BaseModel):
    name: str
    description: str | None = None


class ExperimentConfiguration(BaseModel):
    """Configuration model for the experiment-scope config file."""

    metadata: ExperimentMetadata

    steps: Annotated[
        dict[str, StepConfiguration],
        Field(
            default_factory=list,
            description="List of steps to be executed in the experiment.",
        ),
    ]
