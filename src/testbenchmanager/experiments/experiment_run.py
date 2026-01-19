import logging
from datetime import datetime
from threading import Event, Lock

from testbenchmanager.instruments.virtual import virtual_instrument_registry

from .experiment_context import ExperimentContext as ExperimentContext
from .generic_stateful import GenericStateful
from .state import Outcome, State
from .step import Step
from .step_configuration import StepConfiguration
from .step_registry import step_registry

logger = logging.getLogger(__name__)


from .experiment_configuration import ExperimentConfiguration


class ExperimentRun(GenericStateful):
    def __init__(
        self, config: ExperimentConfiguration, context: ExperimentContext
    ) -> None:
        super().__init__()
        self._context = context
        self.configuration_uid = config.metadata.uid
        self.steps: dict[str, Step[StepConfiguration]] = {}
        self._abort: Event = Event()
        self._abort_lock: Lock = Lock()

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

                raise RuntimeError(
                    f"Step class '{step_config.class_name}' not found in registry."
                ) from e
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
                raise e

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
                    raise RuntimeError(
                        f"Virtual instrument with UID '{uid}' used in step "
                        f"'{step_config.class_name}' not found in registry."
                    ) from e

            self.steps[step.metadata.uid] = step

    def run(self) -> None:
        self.state = State.RUNNING
        for step in self.steps.values():
            with self._abort_lock:
                if self._abort.is_set():
                    if step.skip_on_abort:
                        logger.info(
                            "Skipping step '%s' due to experiment abort.",
                            step.metadata.uid,
                        )
                        step.state = State.COMPLETE
                        step.outcome = Outcome.SKIPPED
                        continue
                elif (
                    step.skip_on_previous_failure
                    and self._get_total_outcome() == Outcome.FAILED
                ):
                    logger.info(
                        "Skipping step '%s' due to previous step failure.",
                        step.metadata.uid,
                    )
                    step.state = State.COMPLETE
                    step.outcome = Outcome.SKIPPED
                    continue
            try:
                step.execute(self._abort)
            except Exception as e:
                logger.error("Error occurred during step execution: %s", e)
                step.state = State.COMPLETE
                step.outcome = Outcome.FAILED
                continue

        self.outcome = self._get_total_outcome()
        self.state = State.COMPLETE
        self.end_time = datetime.now()

    def _get_total_outcome(self) -> Outcome:
        if self._abort.is_set():
            return Outcome.ABORTED
        for step in self.steps.values():
            if step.outcome == Outcome.FAILED:
                return Outcome.FAILED
            if step.outcome == Outcome.ABORTED:
                return Outcome.ABORTED
            if step.outcome == Outcome.SUCCEEDED_WITH_WARNINGS:
                return Outcome.SUCCEEDED_WITH_WARNINGS
        return Outcome.SUCCEEDED

    def stop(self) -> None:
        self._abort.set()
        self.state = State.STOPPING
