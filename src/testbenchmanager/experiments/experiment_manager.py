from logging import getLogger

from yaml import YAMLError

from testbenchmanager.configuration import (
    ConfigurationDirectory,
    ConfigurationManager,
    ConfigurationScope,
)

from .experiment_configuration import ExperimentConfiguration
from .experiment_context import ExperimentContext
from .experiment_run import ExperimentRun
from .experiment_state import ExperimentState
from .run_registry import run_registry

logger = getLogger(__name__)
# TODO: better exception names


class ExperimentManager:

    def inject_configuration_manager(
        self, configuration_manager: ConfigurationManager
    ) -> None:
        self._config_dir = configuration_manager.get_configuration_directory(
            ConfigurationScope.EXPERIMENTS
        )

    def __init__(self) -> None:
        self._config_dir: ConfigurationDirectory | None = None
        self._current_experiment: ExperimentRun | None = None
        self._run_uid_counter: int = 0

    def list_experiments(self) -> list[str]:
        if self._config_dir is None:
            raise RuntimeError(
                "Configuration manager not injected. Cannot list experiments."
            )
        return self._config_dir.configuration_uids

    def _build_experiment_config(self, uid: str) -> ExperimentConfiguration:
        if self._config_dir is None:
            raise RuntimeError(
                "Configuration manager not injected. Cannot build experiment configuration."
            )
        try:
            configuration = ExperimentConfiguration.model_validate(
                self._config_dir.get_contents(uid)
            )
        except (FileNotFoundError, YAMLError) as e:
            logger.info(
                "Failed to load experiment configuration with UID '%s': %s", uid, e
            )
            raise e

        return configuration

    def build_experiment(self, uid: str) -> ExperimentRun:
        return ExperimentRun(self._build_experiment_config(uid), ExperimentContext())

    def add_experiment(self, uid: str) -> str:
        if (
            self._current_experiment is not None
            and self._current_experiment.state == ExperimentState.RUNNING
        ):
            raise RuntimeError(
                "An experiment is already running. It must be stopped first."
            )
        run_uid = str(self._run_uid_counter)
        self._run_uid_counter += 1
        run_registry.register(run_uid, self.build_experiment(uid))

        return run_uid

    def run_experiment(self, run_uid: str) -> None:
        if (
            self._current_experiment is not None
            and self._current_experiment.state == ExperimentState.RUNNING
        ):
            raise RuntimeError(
                "An experiment is already running. It must be stopped first."
            )
        next_experiment = run_registry.get(run_uid)

        if next_experiment.state != ExperimentState.READY:
            raise RuntimeError(
                "Experiment is not in a runnable state. Current state: "
                f"{next_experiment.state}"
            )
        self._current_experiment = next_experiment
        self._current_experiment.run()

    def stop_experiment(self) -> None:
        if self._current_experiment is None:
            raise RuntimeError("No experiment loaded to stop.")

        self._current_experiment.stop()


experiment_manager = ExperimentManager()
