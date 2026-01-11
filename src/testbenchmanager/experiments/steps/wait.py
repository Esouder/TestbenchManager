from datetime import datetime
from multiprocessing import Event
from time import monotonic, sleep

from testbenchmanager.experiments.step import BaseStep
from testbenchmanager.experiments.step_configuration import StepConfiguration
from testbenchmanager.experiments.step_registry import step_registry
from testbenchmanager.experiments.step_state import StepState


class WaitConfiguration(StepConfiguration):
    duration: float  # Duration to wait in seconds


@step_registry.register_class()
class Wait(BaseStep):
    @classmethod
    def configuration(cls) -> type[WaitConfiguration]:
        return WaitConfiguration

    def __init__(self, config: WaitConfiguration) -> None:
        self._duration = config.duration
        self._stop_event = Event()
        super().__init__(config)

    def execute(self) -> None:
        self._state = StepState.RUNNING
        self.start_time = datetime.now()
        timer_start = monotonic()
        while (
            not self._stop_event.is_set()
            and (monotonic() - timer_start) < self._duration
        ):
            sleep(0.1)
        self.end_time = datetime.now()
        self._state = StepState.COMPLETED

    def stop(self) -> None:
        self._stop_event.set()
        self._state = StepState.STOPPING

    def instrument_uids(self) -> list[str]:
        return []
