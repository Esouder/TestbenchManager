from datetime import datetime
from typing import Generic, Protocol, TypeVar

from .step_configuration import StepConfiguration, StepMetadata
from .step_state import StepState

ConfigurationType = TypeVar(
    "ConfigurationType", bound=StepConfiguration, covariant=True
)


class Step(Protocol, Generic[ConfigurationType]):

    _metadata: StepMetadata

    @classmethod
    def configuration(cls) -> type[ConfigurationType]: ...

    @property
    def metadata(self) -> StepMetadata: ...

    @property
    def state(self) -> StepState: ...

    @property
    def start_time(self) -> datetime | None: ...

    @property
    def end_time(self) -> datetime | None: ...

    def __init__(self, config: ConfigurationType) -> None: ...
    def execute(self) -> None:
        """Execute the step."""
        ...

    def stop(self) -> None:
        """Stop the step execution if it's running."""
        ...

    def instrument_uids(self) -> list[str]:
        """Return a list of virtual instrument UIDs used by this step."""
        ...


class BaseStep:
    def __init__(self, config: StepConfiguration) -> None:
        self._metadata = config.metadata
        self._state = StepState.PENDING
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    @property
    def metadata(self) -> StepMetadata:
        return self._metadata

    @property
    def state(self) -> StepState:
        return self._state
