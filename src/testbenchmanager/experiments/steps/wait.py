from datetime import datetime
from threading import Event
from time import monotonic, sleep

from testbenchmanager.experiments.state import Outcome, State
from testbenchmanager.experiments.step import BaseStep
from testbenchmanager.experiments.step_configuration import StepConfiguration
from testbenchmanager.experiments.step_registry import step_registry


class WaitConfiguration(StepConfiguration):
    duration: float  # Duration to wait in seconds


@step_registry.register_class()
class Wait(BaseStep):
    @classmethod
    def configuration(cls) -> type[WaitConfiguration]:
        return WaitConfiguration

    def __init__(self, config: WaitConfiguration) -> None:
        self._duration = config.duration
        super().__init__(config)

    def execute(self, abort_event: Event) -> None:
        self.state = State.RUNNING
        self.start_time = datetime.now()
        timer_start = monotonic()
        while not abort_event.is_set() and (monotonic() - timer_start) < self._duration:
            sleep(0.1)
        self.end_time = datetime.now()

        self.state = State.COMPLETE
        self.outcome = (
            Outcome.SUCCEEDED if not abort_event.is_set() else Outcome.ABORTED
        )

    def instrument_uids(self) -> list[str]:
        return []
