from datetime import datetime
from threading import Event
from typing import Callable, Generic, Protocol, TypeVar

from .generic_stateful import GenericStateful
from .state import Outcome, State
from .step_configuration import StepConfiguration, StepMetadata

ConfigurationType = TypeVar(
    "ConfigurationType", bound=StepConfiguration, covariant=True
)


class Step(Protocol, Generic[ConfigurationType]):

    @classmethod
    def configuration(cls) -> type[ConfigurationType]: ...

    @property
    def outcome(self) -> Outcome | None: ...

    @outcome.setter
    def outcome(self, value: Outcome | None) -> None: ...

    @property
    def state(self) -> State: ...

    @state.setter
    def state(self, value: State) -> None: ...

    @property
    def metadata(self) -> StepMetadata: ...

    @property
    def start_time(self) -> datetime | None: ...

    @property
    def end_time(self) -> datetime | None: ...

    @property
    def skip_on_previous_failure(self) -> bool: ...

    @property
    def skip_on_abort(self) -> bool: ...

    def __init__(self, config: ConfigurationType) -> None: ...

    def execute(self, abort_event: Event) -> None:
        """Execute the step."""
        ...

    def instrument_uids(self) -> list[str]:
        """Return a list of virtual instrument UIDs used by this step."""
        ...

    def subscribe_to_state_change(
        self, callback: Callable[[State], None]
    ) -> Callable[[], None]: ...


class BaseStep(GenericStateful):
    outcome: Outcome | None

    def __init__(self, config: StepConfiguration) -> None:
        super().__init__()
        self.metadata = config.metadata
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.skip_on_previous_failure = config.skip_on_previous_failure
        self.skip_on_abort = config.skip_on_abort
