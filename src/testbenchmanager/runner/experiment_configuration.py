# pylint: skip-file
# TODO: Remove skip-file when possible


from pydantic import BaseModel

from .step import Step


class ExperimentConfigurationMetadata(BaseModel):
    name: str
    description: str | None = None


class ExperimentConfiguration(BaseModel):
    metadata: ExperimentConfigurationMetadata
    instruments: list[str] = []
    parameters: dict[str, str] = {}
    steps: list[Step] = []
