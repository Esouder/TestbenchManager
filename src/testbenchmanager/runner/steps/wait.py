import time
from typing import ClassVar

from testbenchmanager.runner.step import BaseStep
from testbenchmanager.runner.step_registry import step_registry


@step_registry.register_step()
class Wait(BaseStep):
    name: ClassVar[str] = "wait"
    duration: float  # in seconds

    def run(self) -> None:

        time.sleep(self.duration)

    def stop(self) -> None:
        pass
