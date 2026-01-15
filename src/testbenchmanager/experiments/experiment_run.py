import logging
from datetime import datetime
from typing import Callable

from testbenchmanager.instruments.virtual import virtual_instrument_registry

from .experiment_context import ExperimentContext as ExperimentContext
from .experiment_state import ExperimentState
from .step import Step
from .step_configuration import StepConfiguration
from .step_registry import step_registry

logger = logging.getLogger(__name__)


from .experiment_configuration import ExperimentConfiguration


class ExperimentRun:
    def __init__(
        self, config: ExperimentConfiguration, context: ExperimentContext
    ) -> None:
        self._context = context
        self.experiment_metadata = config.metadata
        self.steps: dict[str, Step[StepConfiguration]] = {}
        self._abort: bool = False
        self._stop_method: Callable[[], None] | None = None
        self._state: ExperimentState = ExperimentState.READY
        self._state_subscriber_callbacks: list[Callable[[ExperimentState], None]] = []
        self.current_step: Step[StepConfiguration] | None = None

        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        for step_config in config.steps:
            try:
                step_class = step_registry.get(step_config.class_name)
            except KeyError as e:
                logger.warning(
                    "Step class '%s' not found in registry: %s",
                    step_config.class_name,
                    e,
                )
                self.state = ExperimentState.MALFORMED
                continue
            step_config = step_class.configuration().model_validate(
                step_config.model_dump()
            )
            try:
                step = step_class(step_config)
            except Exception as e:
                logger.error(
                    "Error occurred while instantiating step '%s': %s",
                    step_config.class_name,
                    e,
                )
                self.state = ExperimentState.MALFORMED
                continue

            for uid in step.instrument_uids():
                try:
                    virtual_instrument_registry.get(uid)
                except KeyError as e:
                    logger.warning(
                        "Virtual instrument with UID '%s' used in step '%s' "
                        "not found in registry. Aborting: %s",
                        uid,
                        step_config.class_name,
                        e,
                    )
                    self.state = ExperimentState.MALFORMED
                    continue

            self.steps[step.metadata.uid] = step

    @property
    def state(self) -> ExperimentState:
        return self._state

    @state.setter
    def state(self, value: ExperimentState) -> None:
        self._state = value
        for callback in self._state_subscriber_callbacks:
            callback(value)

    def subscribe_to_state_changes(
        self, callback: Callable[[ExperimentState], None]
    ) -> Callable[[], None]:
        self._state_subscriber_callbacks.append(callback)

        def unsubscribe() -> None:
            self._state_subscriber_callbacks.remove(callback)

        return unsubscribe

    def run(self) -> None:
        if self.state == ExperimentState.MALFORMED:
            raise RuntimeError("Cannot run malformed experiment.")
        self.state = ExperimentState.RUNNING
        for step in self.steps.values():
            self.current_step = step
            self._stop_method = step.stop
            if self._abort:
                logger.info("Experiment run stopped before executing step '%s'.", step)
                break
            try:
                step.execute()
            except Exception as e:
                logger.error("Error occurred during step execution: %s", e)
                # Not sure if this should abort the entire experiment or continue to next step.
                break

        if self._abort:
            self.state = ExperimentState.ABORTED
        else:
            self.state = ExperimentState.COMPLETED

    def stop(self) -> None:
        self._abort = True
        self.state = ExperimentState.STOPPING
        if self._stop_method is not None:
            self._stop_method()
